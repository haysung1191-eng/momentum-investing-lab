import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from news_sidecar_data import build_news_matrices
from us_stock_mom12_1 import load_price_matrix as load_us_price_matrix, load_universe as load_us_universe


def _load_korea_close(price_base: Path) -> pd.DataFrame:
    close_frames = []
    for path in sorted((price_base / "stock").glob("*.csv.gz")):
        code = path.stem.replace(".csv", "")
        df = pd.read_csv(path, compression="gzip", parse_dates=["date"])
        if df.empty:
            continue
        close_frames.append(pd.Series(pd.to_numeric(df["close"], errors="coerce").values, index=pd.to_datetime(df["date"]), name=code))
    if not close_frames:
        return pd.DataFrame()
    return pd.concat(close_frames, axis=1).sort_index()


def _daily_rank_ic(feature: pd.Series, fwd: pd.Series, min_names: int) -> float | None:
    valid = pd.concat([feature, fwd], axis=1).dropna()
    if len(valid) < min_names:
        return None
    if valid.iloc[:, 0].nunique(dropna=True) < 2 or valid.iloc[:, 1].nunique(dropna=True) < 2:
        return None
    x = valid.iloc[:, 0].rank()
    y = valid.iloc[:, 1].rank()
    ic = x.corr(y)
    if pd.isna(ic):
        return None
    return float(ic)


def evaluate_signal(close: pd.DataFrame, feature: pd.DataFrame, signal_name: str, min_names: int) -> dict[str, float | str]:
    close = close.sort_index()
    feature = feature.reindex(close.index)
    trailing = feature.rolling(5, min_periods=1).sum().shift(1)
    covered = feature.notna().rolling(5, min_periods=1).sum().shift(1)
    fwd_5d = close.shift(-5) / close - 1.0

    ics = []
    spreads = []
    top_vals = []
    bottom_vals = []
    covered_counts = []
    for dt in close.index:
        score_row = trailing.loc[dt].where(covered.loc[dt] > 0)
        panel = pd.concat([score_row.rename("score"), fwd_5d.loc[dt].rename("fwd")], axis=1).dropna()
        covered_counts.append(int(len(panel)))
        ic = _daily_rank_ic(score_row, fwd_5d.loc[dt], min_names=min_names)
        if ic is not None:
            ics.append(ic)
        if len(panel) < min_names:
            continue
        if panel["score"].nunique(dropna=True) < 2:
            continue
        panel = panel.sort_values("score")
        q = max(int(len(panel) * 0.2), 1)
        bottom = panel.head(q)["fwd"].mean()
        top = panel.tail(q)["fwd"].mean()
        spreads.append(float(top - bottom))
        top_vals.append(float(top))
        bottom_vals.append(float(bottom))

    start = ""
    end = ""
    raw_covered = feature.dropna(how="all")
    if not raw_covered.empty:
        start = str(raw_covered.index.min().date())
        end = str(raw_covered.index.max().date())
    adequate_days = int(sum(1 for x in covered_counts if x >= min_names))
    adequate_ratio = float(adequate_days / len(close.index)) if len(close.index) > 0 else 0.0
    covered_nonzero = [x for x in covered_counts if x > 0]
    median_covered_nonzero = float(np.median(covered_nonzero)) if covered_nonzero else 0.0
    status = "OK" if adequate_days >= 20 and adequate_ratio >= 0.05 else "INSUFFICIENT_COVERAGE"

    return {
        "Signal": signal_name,
        "CoverageStart": start,
        "CoverageEnd": end,
        "EvalDays": int(len(spreads)),
        "AdequateCoverageDays": adequate_days,
        "AdequateCoverageRatio": adequate_ratio,
        "MedianCoveredNames": float(np.median(covered_counts)) if covered_counts else 0.0,
        "MedianCoveredNamesNonZero": median_covered_nonzero,
        "EvaluationStatus": status,
        "MeanDailyIC": float(np.mean(ics)) if ics else 0.0,
        "MedianDailyIC": float(np.median(ics)) if ics else 0.0,
        "MeanTopQuintileFwd5d": float(np.mean(top_vals)) if top_vals else 0.0,
        "MeanBottomQuintileFwd5d": float(np.mean(bottom_vals)) if bottom_vals else 0.0,
        "MeanTopMinusBottomFwd5d": float(np.mean(spreads)) if spreads else 0.0,
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Evaluate US/KR news sidecar sanity signals against forward returns.")
    p.add_argument("--us-price-base", type=str, default="data/prices_us_stock_sp100")
    p.add_argument("--us-universe", type=str, default="backtests/us_stock_sp100_universe.csv")
    p.add_argument("--us-news-base", type=str, default="data/news_us_hf")
    p.add_argument("--us-out", type=str, default="backtests/us_news_sidecar_signal_eval.csv")
    p.add_argument("--kr-price-base", type=str, default="data/prices_operating_institutional_v1")
    p.add_argument("--kr-news-base", type=str, default="data/news_kis_naver")
    p.add_argument("--kr-out", type=str, default="backtests/kis_news_sidecar_signal_eval.csv")
    p.add_argument("--min-names-us", type=int, default=15)
    p.add_argument("--min-names-kr", type=int, default=10)
    return p.parse_args()


def main() -> None:
    args = parse_args()

    us_universe = load_us_universe(Path(args.us_universe))
    us_close, _ = load_us_price_matrix(Path(args.us_price_base), us_universe)
    us_news = build_news_matrices(args.us_news_base, market="stock")
    us_rows = []
    for col in ["article_count", "title_score"]:
        us_rows.append(evaluate_signal(us_close, us_news.get(col, pd.DataFrame()), col, min_names=args.min_names_us))
    us_df = pd.DataFrame(us_rows)
    us_df.to_csv(args.us_out, index=False)

    kr_close = _load_korea_close(Path(args.kr_price_base))
    kr_news = build_news_matrices(args.kr_news_base, market="stock")
    kr_rows = []
    for col in ["article_count", "title_score"]:
        kr_rows.append(evaluate_signal(kr_close, kr_news.get(col, pd.DataFrame()), col, min_names=args.min_names_kr))
    kr_df = pd.DataFrame(kr_rows)
    kr_df.to_csv(args.kr_out, index=False)

    print("US")
    print(us_df.to_string(index=False))
    print()
    print("KR")
    print(kr_df.to_string(index=False))


if __name__ == "__main__":
    main()
