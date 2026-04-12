import os
import time
from io import BytesIO, StringIO
from typing import Dict, List

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup


FN_GUIDE_RATIO_URL = "https://comp.fnguide.com/SVO2/ASP/SVD_FinanceRatio.asp"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"


def default_quality_base() -> str:
    return "data/quality_fnguide"


def _safe_numeric(value: object) -> float:
    if value is None:
        return np.nan
    text = str(value).strip()
    if not text or text in {"nan", "None", "N/A", "-"}:
        return np.nan
    text = text.replace(",", "").replace("%", "")
    try:
        return float(text)
    except Exception:
        return np.nan


def _period_end_from_label(label: str) -> pd.Timestamp | None:
    text = str(label).strip()
    if "/" not in text:
        return None
    try:
        year, month = text.split("/")[:2]
        return pd.Timestamp(int(year), int(month), 1) + pd.offsets.MonthEnd(0)
    except Exception:
        return None


def _effective_date(period_end: pd.Timestamp, quarterly: bool) -> pd.Timestamp:
    lag_days = 45 if quarterly else 90
    return period_end + pd.Timedelta(days=lag_days)


def _extract_row(df: pd.DataFrame, keyword: str) -> pd.Series | None:
    first_col = df.columns[0]
    mask = df[first_col].astype(str).str.contains(keyword, na=False)
    if not mask.any():
        return None
    row = df.loc[mask].iloc[0]
    return row.iloc[1:]


def _parse_ratio_tables(html: str) -> List[pd.DataFrame]:
    soup = BeautifulSoup(html, "lxml")
    out: List[pd.DataFrame] = []
    for table in soup.find_all("table"):
        try:
            out.append(pd.read_html(StringIO(str(table)))[0])
        except Exception:
            continue
    return out


def fetch_quality_events(code: str, pause_sec: float = 0.15) -> pd.DataFrame:
    params = {
        "pGB": "1",
        "gicode": f"A{code}",
        "cID": "",
        "MenuYn": "Y",
        "ReportGB": "",
        "NewMenuID": "104",
        "stkGb": "701",
    }
    resp = requests.get(FN_GUIDE_RATIO_URL, params=params, headers={"User-Agent": USER_AGENT}, timeout=20)
    resp.raise_for_status()
    tables = _parse_ratio_tables(resp.text)
    if len(tables) < 2:
        raise RuntimeError(f"Could not parse FnGuide ratio tables for {code}.")

    annual = tables[0].copy()
    quarterly = tables[1].copy()
    annual.columns = [str(c).strip() for c in annual.columns]
    quarterly.columns = [str(c).strip() for c in quarterly.columns]

    annual_rows = {
        "roe": _extract_row(annual, "ROE"),
        "roa": _extract_row(annual, "ROA"),
        "gross_margin": _extract_row(annual, "매출총이익율"),
        "debt_ratio": _extract_row(annual, "부채비율"),
        "op_margin": _extract_row(annual, "영업이익률"),
    }
    quarterly_rows = {
        "op_margin": _extract_row(quarterly, "영업이익률"),
        "sales_growth": _extract_row(quarterly, "매출액증가율"),
        "eps_growth": _extract_row(quarterly, "EPS증가율"),
    }

    records: List[dict] = []
    for col in annual.columns[1:]:
        period_end = _period_end_from_label(col)
        if period_end is None:
            continue
        rec = {
            "effective_date": _effective_date(period_end, quarterly=False),
            "period_end": period_end,
            "period_label": col,
            "period_type": "annual",
        }
        any_value = False
        for key, row in annual_rows.items():
            value = _safe_numeric(row.get(col)) if row is not None else np.nan
            rec[key] = value
            any_value = any_value or pd.notna(value)
        if any_value:
            records.append(rec)

    for col in quarterly.columns[1:]:
        period_end = _period_end_from_label(col)
        if period_end is None:
            continue
        rec = {
            "effective_date": _effective_date(period_end, quarterly=True),
            "period_end": period_end,
            "period_label": col,
            "period_type": "quarterly",
        }
        any_value = False
        for key, row in quarterly_rows.items():
            value = _safe_numeric(row.get(col)) if row is not None else np.nan
            rec[key] = value
            any_value = any_value or pd.notna(value)
        if any_value:
            records.append(rec)

    out = pd.DataFrame.from_records(records)
    if out.empty:
        raise RuntimeError(f"No quality records extracted for {code}.")
    out = out.sort_values(["effective_date", "period_end", "period_type"]).drop_duplicates(
        subset=["effective_date", "period_type"], keep="last"
    )
    out.insert(0, "ticker", f"S_{code.zfill(6)}")
    if pause_sec > 0:
        time.sleep(pause_sec)
    return out.reset_index(drop=True)


def write_quality_events(df: pd.DataFrame, save_path: str) -> None:
    parent = os.path.dirname(save_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    df.to_csv(save_path, index=False, encoding="utf-8-sig", compression="gzip")


def read_quality_events(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(
        path,
        compression="gzip",
        parse_dates=["effective_date", "period_end"],
    )


def build_quality_matrices(base: str, close_index: pd.Index, tickers: List[str]) -> Dict[str, pd.DataFrame]:
    stock_tickers = [t for t in tickers if str(t).startswith("S_")]
    metrics = ["roe", "roa", "gross_margin", "debt_ratio", "op_margin", "sales_growth", "eps_growth"]
    empty = {m: pd.DataFrame(index=close_index, columns=stock_tickers, dtype=float) for m in metrics}
    rows: List[pd.DataFrame] = []
    for ticker in stock_tickers:
        code = ticker.replace("S_", "")
        path = os.path.join(base, "stock", f"{code}.csv.gz")
        df = read_quality_events(path)
        if df.empty:
            continue
        df = df.copy()
        df["ticker"] = ticker
        rows.append(df)
    if not rows:
        return empty

    long_df = pd.concat(rows, ignore_index=True)
    out: Dict[str, pd.DataFrame] = {}
    for metric in metrics:
        if metric not in long_df.columns:
            out[metric] = empty[metric]
            continue
        pivot = (
            long_df[["effective_date", "ticker", metric]]
            .dropna(subset=[metric])
            .pivot_table(index="effective_date", columns="ticker", values=metric, aggfunc="last")
            .sort_index()
        )
        mat = pivot.reindex(close_index).ffill().reindex(columns=stock_tickers)
        out[metric] = mat
    return out


def compute_quality_score_frame(index: pd.Index, quality_mats: Dict[str, pd.DataFrame], dt: pd.Timestamp) -> pd.DataFrame:
    frame = pd.DataFrame(index=index)
    metric_weights = {
        "roe": 1.00,
        "roa": 0.50,
        "gross_margin": 0.75,
        "op_margin": 0.50,
        "sales_growth": 0.25,
        "eps_growth": 0.25,
        "debt_ratio": -0.75,
    }
    weighted_parts: List[pd.Series] = []
    weight_total = 0.0
    coverage = pd.Series(0.0, index=index)
    for metric, weight in metric_weights.items():
        mat = quality_mats.get(metric)
        if mat is None or dt not in mat.index:
            continue
        series = pd.to_numeric(mat.loc[dt].reindex(index), errors="coerce")
        valid = series.dropna()
        if len(valid) < 5:
            continue
        std = float(valid.std(ddof=0))
        if std <= 0 or not np.isfinite(std):
            continue
        z = (series - float(valid.mean())) / std
        frame[metric] = series
        weighted_parts.append(z.fillna(0.0) * float(weight))
        coverage = coverage + series.notna().astype(float)
        weight_total += abs(float(weight))
    if not weighted_parts or weight_total <= 0:
        return frame.iloc[0:0]
    composite = sum(weighted_parts) / weight_total
    frame["quality_score"] = composite
    frame["quality_coverage"] = coverage
    return frame


def rank_quality_at(
    feat: Dict[str, pd.DataFrame],
    quality_mats: Dict[str, pd.DataFrame],
    dt: pd.Timestamp,
    eligible_mask: pd.DataFrame | None,
    close_s: pd.DataFrame,
    trend_ma: int,
    prev_holds: List[str],
    top_k: int,
    hold_buffer: int,
) -> pd.DataFrame:
    base = pd.DataFrame({k: v.loc[dt] for k, v in feat.items()}).dropna()
    if base.empty:
        return base
    base = base[np.isfinite(base).all(axis=1)]
    if base.empty:
        return base
    q = compute_quality_score_frame(base.index, quality_mats, dt)
    if q.empty:
        return q
    df = base.join(q[["quality_score", "quality_coverage"]], how="inner")
    df = df[df["quality_coverage"] >= 2]
    if df.empty:
        return df
    if eligible_mask is not None and dt in eligible_mask.index:
        eligible = eligible_mask.loc[dt].fillna(False)
        df = df.loc[df.index.intersection(eligible[eligible].index)]
        if df.empty:
            return df
    if trend_ma > 0:
        ma = close_s.rolling(trend_ma, min_periods=trend_ma).mean()
        if dt in ma.index and dt in close_s.index:
            trend_ok = close_s.loc[dt].reindex(df.index) > ma.loc[dt].reindex(df.index)
            df = df.loc[df.index.intersection(trend_ok[trend_ok.fillna(False)].index)]
            if df.empty:
                return df
    df["buy_score"] = 50.0 + 10.0 * df["quality_score"]
    df["buy_score"] = df["buy_score"].clip(lower=0.1)
    df["overheat"] = "정상"
    ranked = df.sort_values(["quality_score", "avg_mom"], ascending=[False, False])
    buffer_limit = max(1, int(top_k)) + max(0, int(hold_buffer))
    entry = list(ranked.head(max(1, int(top_k))).index)
    survivors = [ticker for ticker in prev_holds if ticker in set(ranked.head(buffer_limit).index)]
    picks = list(dict.fromkeys(entry + survivors))
    return ranked.loc[ranked.index.intersection(picks)].head(buffer_limit)
