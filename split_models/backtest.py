from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from split_models.pipeline import (
    PipelineConfig,
    _load_kr_listing,
    _load_us_listing,
    _normalize_target_weight,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output" / "split_models_backtest"


@dataclass(frozen=True)
class BacktestConfig:
    signal_start: str = "2020-01-31"
    one_way_cost_bps: float = 10.0
    top_country_count: int = 2
    top_sector_count: int = 3
    trading_book_size: int = 12
    trading_book_market_cap: int = 6
    trading_book_weight_cap: float = 0.12
    tenbagger_book_size: int = 8
    tenbagger_weight_cap: float = 0.06
    us_min_median_value: float = 25_000_000.0
    kr_min_median_value: float = 2_000_000_000.0
    min_price: float = 5.0
    baseline_variant: str = "equal_weight_no_mad"


@dataclass(frozen=True)
class TradingVariant:
    name: str
    use_flow_filter: bool = True
    use_sector_filter: bool = True
    use_mad_weighting: bool = True
    min_holdings: int = 0
    hold_buffer: int = 0
    blacklist_symbols: tuple[str, ...] = ()
    exclude_kr_unknown_stocks: bool = False
    us_flow_score_cap: float | None = None
    min_rel_volume: float | None = None
    max_r1m: float | None = None
    soft_max_r1m: float | None = None
    soft_r1m_penalty: float = 1.0
    entry_soft_max_r1m: float | None = None
    entry_soft_r1m_penalty: float = 1.0
    max_positions_per_sector: int | None = None
    breadth_risk_off_threshold: int | None = None
    breadth_risk_off_exposure: float = 1.0
    sector_risk_off_name: str | None = None
    sector_risk_off_weight_threshold: float | None = None
    sector_risk_off_exposure: float = 1.0


def _normalize_weight_series(weights: pd.Series) -> pd.Series:
    out = pd.to_numeric(weights, errors="coerce").fillna(0.0).clip(lower=0.0)
    total = float(out.sum())
    if total <= 0:
        return pd.Series(np.repeat(0.0, len(out)), index=out.index)
    return out / total


def _variant_specs() -> list[TradingVariant]:
    return [
        TradingVariant(name="default", use_flow_filter=True, use_sector_filter=True, use_mad_weighting=True),
        TradingVariant(name="no_flow_filter", use_flow_filter=False, use_sector_filter=True, use_mad_weighting=True),
        TradingVariant(name="no_sector_filter", use_flow_filter=True, use_sector_filter=False, use_mad_weighting=True),
        TradingVariant(name="equal_weight_no_mad", use_flow_filter=True, use_sector_filter=True, use_mad_weighting=False),
        TradingVariant(name="equal_weight_no_mad_min4", use_flow_filter=True, use_sector_filter=True, use_mad_weighting=False, min_holdings=4),
        TradingVariant(
            name="rule_kr_unknown_off",
            use_flow_filter=True,
            use_sector_filter=False,
            use_mad_weighting=True,
            exclude_kr_unknown_stocks=True,
        ),
        TradingVariant(
            name="rule_us_flow_cap",
            use_flow_filter=True,
            use_sector_filter=False,
            use_mad_weighting=True,
            us_flow_score_cap=0.30,
        ),
        TradingVariant(
            name="rule_combo_generalized",
            use_flow_filter=True,
            use_sector_filter=False,
            use_mad_weighting=True,
            exclude_kr_unknown_stocks=True,
            us_flow_score_cap=0.30,
        ),
    ]


def _variant_map() -> dict[str, TradingVariant]:
    return {variant.name: variant for variant in _variant_specs()}


def _baseline_variant_map() -> dict[str, TradingVariant]:
    variants = {variant.name: variant for variant in _variant_specs()}
    variants.update(
        {
            "rule_trend_chase_cap": TradingVariant(
                name="rule_trend_chase_cap",
                use_flow_filter=True,
                use_sector_filter=True,
                use_mad_weighting=False,
                min_holdings=4,
                max_r1m=0.20,
            ),
            "rule_trend_chase_soft": TradingVariant(
                name="rule_trend_chase_soft",
                use_flow_filter=True,
                use_sector_filter=True,
                use_mad_weighting=False,
                min_holdings=4,
                soft_max_r1m=0.20,
                soft_r1m_penalty=0.5,
            ),
            "rule_trend_chase_entry_soft": TradingVariant(
                name="rule_trend_chase_entry_soft",
                use_flow_filter=True,
                use_sector_filter=True,
                use_mad_weighting=False,
                min_holdings=4,
                entry_soft_max_r1m=0.20,
                entry_soft_r1m_penalty=0.5,
            ),
            "rule_sector_cap2": TradingVariant(
                name="rule_sector_cap2",
                use_flow_filter=True,
                use_sector_filter=True,
                use_mad_weighting=False,
                min_holdings=4,
                max_positions_per_sector=2,
            ),
            "rule_breadth_risk_off": TradingVariant(
                name="rule_breadth_risk_off",
                use_flow_filter=True,
                use_sector_filter=True,
                use_mad_weighting=False,
                min_holdings=4,
                breadth_risk_off_threshold=4,
                breadth_risk_off_exposure=0.75,
            ),
            "rule_breadth_risk_off_080": TradingVariant(
                name="rule_breadth_risk_off_080",
                use_flow_filter=True,
                use_sector_filter=True,
                use_mad_weighting=False,
                min_holdings=4,
                breadth_risk_off_threshold=4,
                breadth_risk_off_exposure=0.80,
            ),
            "rule_breadth_it_risk_off": TradingVariant(
                name="rule_breadth_it_risk_off",
                use_flow_filter=True,
                use_sector_filter=True,
                use_mad_weighting=False,
                min_holdings=4,
                breadth_risk_off_threshold=4,
                breadth_risk_off_exposure=0.75,
                sector_risk_off_name="Information Technology",
                sector_risk_off_weight_threshold=0.55,
                sector_risk_off_exposure=0.80,
            ),
            "rule_sector_cap2_breadth_risk_off": TradingVariant(
                name="rule_sector_cap2_breadth_risk_off",
                use_flow_filter=True,
                use_sector_filter=True,
                use_mad_weighting=False,
                min_holdings=4,
                max_positions_per_sector=2,
                breadth_risk_off_threshold=4,
                breadth_risk_off_exposure=0.75,
            ),
            "rule_sector_cap2_breadth_it_risk_off": TradingVariant(
                name="rule_sector_cap2_breadth_it_risk_off",
                use_flow_filter=True,
                use_sector_filter=True,
                use_mad_weighting=False,
                min_holdings=4,
                max_positions_per_sector=2,
                breadth_risk_off_threshold=4,
                breadth_risk_off_exposure=0.75,
                sector_risk_off_name="Information Technology",
                sector_risk_off_weight_threshold=0.55,
                sector_risk_off_exposure=0.80,
            ),
        }
    )
    return variants


def _summarize_returns(returns: pd.Series, dates: pd.Series | None = None) -> dict[str, float]:
    r = pd.to_numeric(returns, errors="coerce").dropna()
    if r.empty:
        return {"CAGR": np.nan, "MDD": np.nan, "Sharpe": np.nan, "FinalNAV": np.nan}
    nav = (1.0 + r).cumprod()
    if dates is not None:
        d = pd.to_datetime(dates).dropna()
        years = max((d.iloc[-1] - d.iloc[0]).days / 365.25, 1.0 / 12.0) if len(d) >= 2 else max(len(r) / 12.0, 1.0 / 12.0)
    else:
        years = max(len(r) / 12.0, 1.0 / 12.0)
    return {
        "CAGR": float(nav.iloc[-1] ** (1.0 / years) - 1.0),
        "MDD": _max_drawdown(nav),
        "Sharpe": _monthly_sharpe(r),
        "FinalNAV": float(nav.iloc[-1]),
    }


def _monthly_sharpe(monthly_returns: pd.Series) -> float:
    r = pd.to_numeric(monthly_returns, errors="coerce").dropna()
    if len(r) < 2:
        return 0.0
    vol = float(r.std(ddof=0))
    if vol <= 0:
        return 0.0
    return float(r.mean() / vol * np.sqrt(12.0))


def _max_drawdown(nav: pd.Series) -> float:
    peak = nav.cummax()
    dd = nav / peak - 1.0
    return float(dd.min()) if not dd.empty else 0.0


def _asset_key(market: str, asset_type: str, symbol: str) -> str:
    return f"{market}:{asset_type}:{symbol}"


def _load_us_universe() -> tuple[pd.DataFrame, pd.DataFrame]:
    stocks = _load_us_listing().copy()
    stocks["Market"] = "US"
    stocks["AssetType"] = "STOCK"
    stocks["Symbol"] = stocks["Symbol"].astype(str)
    stocks["AssetKey"] = [_asset_key("US", "STOCK", sym) for sym in stocks["Symbol"]]

    etfs = pd.read_csv(ROOT / "backtests" / "us_etf_core_universe.csv").copy()
    sector_map = {
        "XLK": "Information Technology",
        "XLF": "Financials",
        "XLE": "Energy",
        "XLV": "Health Care",
        "XLI": "Industrials",
        "XLP": "Consumer Staples",
        "XLY": "Consumer Discretionary",
        "SPY": "Broad Market",
        "QQQ": "Broad Market",
        "IWM": "Broad Market",
        "DIA": "Broad Market",
        "TLT": "Rates",
        "IEF": "Rates",
        "SHY": "Rates",
        "GLD": "Real Assets",
        "VNQ": "Real Estate",
        "HYG": "Credit",
        "LQD": "Credit",
    }
    etfs["Market"] = "US"
    etfs["AssetType"] = "ETF"
    etfs["Symbol"] = etfs["Ticker"].astype(str)
    etfs["Name"] = etfs["Name"].astype(str)
    etfs["Sector"] = etfs["Symbol"].map(sector_map).fillna("ETF")
    etfs["AssetKey"] = [_asset_key("US", "ETF", sym) for sym in etfs["Symbol"]]
    return stocks[["Market", "AssetType", "Symbol", "Name", "Sector", "AssetKey"]], etfs[
        ["Market", "AssetType", "Symbol", "Name", "Sector", "AssetKey"]
    ]


def _load_kr_universe() -> pd.DataFrame:
    universe = pd.read_csv(ROOT / "backtests" / "kis_operating_universe_candidates_institutional_v1.csv").copy()
    universe["Code"] = universe["Code"].astype(str).str.zfill(6)
    stock_codes = universe[universe["Market"].astype(str).eq("STOCK")]["Code"].tolist()
    etf_codes = universe[universe["Market"].astype(str).eq("ETF")]["Code"].tolist()
    listing = _load_kr_listing(stock_codes, etf_codes)
    rows = []
    for row in universe.itertuples(index=False):
        code = str(row.Code).zfill(6)
        asset_type = str(row.Market)
        meta = listing[(listing["Symbol"] == code) & (listing["Market"] == asset_type)]
        if meta.empty:
            meta = listing[listing["Symbol"] == code]
        name = str(meta.iloc[0]["Name"]) if not meta.empty else code
        sector = str(meta.iloc[0]["Sector"]) if not meta.empty else ("ETF" if asset_type == "ETF" else "Unknown")
        rows.append(
            {
                "Market": "KR",
                "AssetType": asset_type,
                "Symbol": code,
                "Name": name,
                "Sector": sector,
                "AssetKey": _asset_key("KR", asset_type, code),
            }
        )
    return pd.DataFrame(rows)


def _price_path(row: pd.Series) -> Path:
    if row["Market"] == "US" and row["AssetType"] == "STOCK":
        return ROOT / "data" / "prices_us_stock_sp100_pitwiki" / "stock" / f"{row['Symbol']}.csv.gz"
    if row["Market"] == "US" and row["AssetType"] == "ETF":
        return ROOT / "data" / "prices_us_etf_core" / "etf" / f"{row['Symbol']}.csv.gz"
    subdir = "etf" if row["AssetType"] == "ETF" else "stock"
    return ROOT / "data" / "prices_operating_institutional_v1" / subdir / f"{row['Symbol']}.csv.gz"


def _flow_path(row: pd.Series) -> Path | None:
    if row["Market"] == "KR" and row["AssetType"] == "STOCK":
        return ROOT / "data" / "flows_operating_institutional_v1" / "stock" / f"{row['Symbol']}.csv.gz"
    return None


def _read_monthly_close(path: Path) -> pd.Series | None:
    if not path.exists():
        return None
    df = pd.read_csv(path, compression="gzip", parse_dates=["date"])
    if df.empty:
        return None
    df = df.rename(columns=str.lower)
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["date", "close"])
    df = df[df["close"] > 0].sort_values("date")
    month_end = df.groupby(df["date"].dt.to_period("M")).tail(1).copy()
    if month_end.empty:
        return None
    return pd.Series(month_end["close"].values, index=pd.to_datetime(month_end["date"]), name=path.stem.replace(".csv", ""))


def _read_daily_frame(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    df = pd.read_csv(path, compression="gzip", parse_dates=["date"])
    if df.empty:
        return None
    df = df.rename(columns=str.lower)
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0.0)
    df = df.dropna(subset=["date", "close"])
    df = df[df["close"] > 0].sort_values("date").drop_duplicates(subset=["date"]).reset_index(drop=True)
    return df


def _build_daily_caches(universe: pd.DataFrame) -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame]]:
    price_cache: dict[str, pd.DataFrame] = {}
    flow_cache: dict[str, pd.DataFrame] = {}
    for row in universe.itertuples(index=False):
        price_df = _read_daily_frame(_price_path(pd.Series(row._asdict())))
        if price_df is not None and not price_df.empty:
            price_cache[row.AssetKey] = price_df
        flow_path = _flow_path(pd.Series(row._asdict()))
        if flow_path is not None and flow_path.exists():
            flow_df = pd.read_csv(flow_path, compression="gzip", parse_dates=["date"]).sort_values("date")
            if not flow_df.empty:
                flow_cache[row.AssetKey] = flow_df
    return price_cache, flow_cache


def _build_monthly_close_matrix(universe: pd.DataFrame, price_cache: dict[str, pd.DataFrame]) -> pd.DataFrame:
    series = []
    for row in universe.itertuples(index=False):
        price_df = price_cache.get(row.AssetKey)
        if price_df is None or price_df.empty:
            continue
        month_end = price_df.groupby(price_df["date"].dt.to_period("M")).tail(1).copy()
        if month_end.empty:
            continue
        s = pd.Series(month_end["close"].values, index=pd.to_datetime(month_end["date"]), name=row.AssetKey)
        s.name = row.AssetKey
        series.append(s)
    return pd.concat(series, axis=1).sort_index() if series else pd.DataFrame()


def _signal_dates(monthly_close: pd.DataFrame, start: str) -> list[pd.Timestamp]:
    required = [
        _asset_key("US", "ETF", "SPY"),
        _asset_key("US", "ETF", "EFA"),
        _asset_key("US", "ETF", "EEM"),
        _asset_key("KR", "ETF", "069500"),
    ]
    available = [col for col in required if col in monthly_close.columns]
    base = monthly_close[available].dropna(how="any") if available else monthly_close.copy()
    dates = [pd.Timestamp(dt) for dt in base.index if pd.Timestamp(dt) >= pd.Timestamp(start)]
    return dates


def _current_pipeline_config(cfg: BacktestConfig) -> PipelineConfig:
    return PipelineConfig(
        top_country_count=cfg.top_country_count,
        top_sector_count=cfg.top_sector_count,
        trading_book_size=cfg.trading_book_size,
        trading_book_market_cap=cfg.trading_book_market_cap,
        trading_book_weight_cap=cfg.trading_book_weight_cap,
        tenbagger_book_size=cfg.tenbagger_book_size,
        tenbagger_weight_cap=cfg.tenbagger_weight_cap,
        us_min_median_value=cfg.us_min_median_value,
        kr_min_median_value=cfg.kr_min_median_value,
        min_price=cfg.min_price,
    )


def _rolling_mad(series: pd.Series, window: int = 63) -> float:
    returns = series.pct_change(fill_method=None).dropna()
    if len(returns) < window:
        return np.nan
    sample = returns.iloc[-window:]
    median = float(sample.median())
    return float((sample - median).abs().median())


def _safe_return(close: pd.Series, days: int) -> float:
    if len(close) <= days:
        return np.nan
    base = float(close.iloc[-days - 1])
    if base <= 0:
        return np.nan
    return float(close.iloc[-1] / base - 1.0)


def _compute_metrics_from_frames(
    row: pd.Series,
    px: pd.DataFrame,
    flow_df: pd.DataFrame | None,
) -> dict | None:
    if px is None or px.empty or len(px) < 252:
        return None
    close = px["close"]
    value = px["close"] * px["volume"]
    current = float(close.iloc[-1])
    ma50 = float(close.tail(50).mean())
    ma200 = float(close.tail(200).mean())
    avg_volume_20 = float(px["volume"].tail(20).mean()) if len(px) >= 20 else np.nan
    avg_volume_60 = float(px["volume"].tail(60).mean()) if len(px) >= 60 else np.nan
    rel_volume = avg_volume_20 / avg_volume_60 if avg_volume_60 and avg_volume_60 > 0 else np.nan
    high_252 = float(close.tail(252).max())
    dist_to_high = current / high_252 - 1.0 if high_252 > 0 else np.nan
    flow_score = np.nan
    flow_accel = np.nan
    if row["Market"] == "KR" and flow_df is not None and not flow_df.empty:
        merged = px.merge(flow_df, on="date", how="inner")
        if len(merged) >= 60:
            traded_value = (merged["close"] * merged["volume"]).replace(0.0, np.nan)
            foreign_notional = merged["foreign_net_volume"] * merged["close"]
            inst_notional = merged["institution_net_volume"] * merged["close"]
            denom20 = traded_value.tail(20).sum()
            foreign_20 = float(foreign_notional.tail(20).sum() / denom20) if denom20 else np.nan
            inst_20 = float(inst_notional.tail(20).sum() / denom20) if denom20 else np.nan
            foreign_ratio_delta = float(merged["foreign_ratio"].iloc[-1] - merged["foreign_ratio"].iloc[-21]) if len(merged) > 21 else np.nan
            flow_score = np.nanmean([foreign_20, 0.5 * inst_20, 0.1 * foreign_ratio_delta])
            flow_accel = foreign_ratio_delta
    elif row["Market"] == "US":
        vol_bonus = max(rel_volume - 1.0, 0.0) if pd.notna(rel_volume) else np.nan
        flow_score = np.nanmean([_safe_return(close, 63), _safe_return(close, 126), vol_bonus, dist_to_high])
        flow_accel = vol_bonus

    r1m = _safe_return(close, 21)
    r3m = _safe_return(close, 63)
    r6m = _safe_return(close, 126)
    r12m = _safe_return(close, 252)
    momentum_score = np.nanmean([0.20 * r1m, 0.30 * r3m, 0.30 * r6m, 0.20 * r12m])
    return {
        "AsOfDate": px["date"].iloc[-1].strftime("%Y-%m-%d"),
        "Market": row["Market"],
        "AssetType": row["AssetType"],
        "Symbol": row["Symbol"],
        "Name": row["Name"],
        "Sector": row["Sector"],
        "AssetKey": row["AssetKey"],
        "CurrentPrice": current,
        "MedianDailyValue60D": float(value.tail(60).median()) if len(value) >= 60 else np.nan,
        "AvgDailyValue20D": float(value.tail(20).mean()) if len(value) >= 20 else np.nan,
        "RelVolume20D60D": rel_volume,
        "R1M": r1m,
        "R3M": r3m,
        "R6M": r6m,
        "R12M": r12m,
        "MA50": ma50,
        "MA200": ma200,
        "TrendOK": int(current > ma50 and ma50 > ma200),
        "MAD63": _rolling_mad(close, window=63),
        "DistanceTo52WHigh": dist_to_high,
        "FlowScore": flow_score,
        "FlowAcceleration": flow_accel,
        "MomentumScore": momentum_score,
    }


def _historical_metrics(
    universe: pd.DataFrame,
    price_cache: dict[str, pd.DataFrame],
    flow_cache: dict[str, pd.DataFrame],
    signal_date: pd.Timestamp,
) -> pd.DataFrame:
    rows = []
    for row in universe.itertuples(index=False):
        price_df = price_cache.get(row.AssetKey)
        if price_df is None or price_df.empty:
            continue
        truncated = price_df[price_df["date"] <= signal_date].copy()
        if len(truncated) < 252:
            continue
        flow_df = flow_cache.get(row.AssetKey)
        if flow_df is not None:
            flow_df = flow_df[flow_df["date"] <= signal_date].copy()
        item = _compute_metrics_from_frames(pd.Series(row._asdict()), truncated, flow_df)
        if item is None:
            continue
        rows.append(item)
    return pd.DataFrame(rows)


def _historical_flow_snapshot(
    metrics: pd.DataFrame,
    monthly_close: pd.DataFrame,
    signal_date: pd.Timestamp,
    cfg: BacktestConfig,
) -> pd.DataFrame:
    country_map = {
        "US": _asset_key("US", "ETF", "SPY"),
        "Developed ex-US": _asset_key("US", "ETF", "EFA"),
        "Emerging": _asset_key("US", "ETF", "EEM"),
        "Korea": _asset_key("KR", "ETF", "069500"),
    }
    country_rows = []
    scores: dict[str, float] = {}
    for label, key in country_map.items():
        if key not in monthly_close.columns or signal_date not in monthly_close.index:
            continue
        idx = monthly_close.index.get_loc(signal_date)
        if idx < 3:
            continue
        base = float(monthly_close.iloc[idx - 3][key])
        now = float(monthly_close.iloc[idx][key])
        if base > 0:
            scores[label] = now / base - 1.0
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    for rank, (label, score) in enumerate(ranked, start=1):
        country_rows.append(
            {
                "AsOfDate": signal_date.strftime("%Y-%m-%d"),
                "ScopeType": "COUNTRY",
                "Market": "GLOBAL",
                "Label": label,
                "FlowScore": score,
                "Rank": rank,
            }
        )

    sector_rows = []
    us = metrics[(metrics["Market"] == "US") & (metrics["AssetType"] == "STOCK")].copy()
    us["Sector"] = us["Sector"].astype(str).replace({"": "Unknown", "nan": "Unknown"})
    known = us[~us["Sector"].isin(["Unknown"])].copy()
    if not known.empty:
        grouped = (
            known.groupby("Sector")
            .agg(MomentumScore=("MomentumScore", "median"), FlowScore=("FlowScore", "median"), Count=("Symbol", "count"))
            .reset_index()
        )
        grouped["Score"] = grouped["MomentumScore"].fillna(0.0) + 0.5 * grouped["FlowScore"].fillna(0.0) + 0.01 * grouped["Count"]
        grouped = grouped.sort_values(["Score", "Sector"], ascending=[False, True]).head(cfg.top_sector_count).reset_index(drop=True)
        grouped["Rank"] = range(1, len(grouped) + 1)
        for row in grouped.itertuples(index=False):
            sector_rows.append(
                {
                    "AsOfDate": signal_date.strftime("%Y-%m-%d"),
                    "ScopeType": "SECTOR",
                    "Market": "US",
                    "Label": row.Sector,
                    "FlowScore": row.Score,
                    "Rank": row.Rank,
                }
            )

    kr_rows = metrics[(metrics["Market"] == "KR") & (metrics["AssetType"] == "STOCK")]
    if not kr_rows.empty:
        sector_rows.append(
            {
                "AsOfDate": signal_date.strftime("%Y-%m-%d"),
                "ScopeType": "SECTOR",
                "Market": "KR",
                "Label": "KR_LEADERS",
                "FlowScore": float(kr_rows["MomentumScore"].median() + 0.5 * kr_rows["FlowScore"].median()),
                "Rank": 1,
            }
        )
    return pd.DataFrame(country_rows + sector_rows)


def _allowed_labels(flow_snapshot: pd.DataFrame, cfg: BacktestConfig) -> tuple[set[str], dict[str, set[str]]]:
    countries = set(
        flow_snapshot[flow_snapshot["ScopeType"] == "COUNTRY"].sort_values("Rank").head(cfg.top_country_count)["Label"].tolist()
    )
    sectors: dict[str, set[str]] = {}
    for market, group in flow_snapshot[flow_snapshot["ScopeType"] == "SECTOR"].groupby("Market"):
        sectors[market] = set(group.sort_values("Rank").head(cfg.top_sector_count)["Label"].tolist())
    return countries, sectors


def _build_momentum_candidates_for_date(
    metrics: pd.DataFrame,
    flow_snapshot: pd.DataFrame,
    cfg: BacktestConfig,
    variant: TradingVariant | None = None,
    prev_hold_keys: set[str] | None = None,
) -> pd.DataFrame:
    variant = variant or TradingVariant(name="default")
    prev_hold_keys = prev_hold_keys or set()
    countries, sectors = _allowed_labels(flow_snapshot, cfg)
    df = metrics.copy()
    if variant.blacklist_symbols:
        df = df[~df["Symbol"].astype(str).isin(set(variant.blacklist_symbols))].copy()
    if variant.exclude_kr_unknown_stocks:
        df = df[~((df["Market"] == "KR") & (df["AssetType"] == "STOCK") & (df["Sector"].astype(str) == "Unknown"))].copy()
    if variant.us_flow_score_cap is not None:
        df = df[~((df["Market"] == "US") & (df["FlowScore"] > float(variant.us_flow_score_cap)))].copy()
    if variant.min_rel_volume is not None:
        df = df[(df["RelVolume20D60D"].fillna(0.0) >= float(variant.min_rel_volume))].copy()
    if variant.max_r1m is not None:
        df = df[(df["R1M"].fillna(0.0) <= float(variant.max_r1m))].copy()
    df["CountryLabel"] = np.where(df["Market"].eq("US"), "US", "Korea")
    df["CountryAligned"] = df["CountryLabel"].isin(countries).astype(int)
    df["SectorAligned"] = [
        int(
            (not variant.use_sector_filter)
            or (row.Sector in sectors.get(str(row.Market), set()))
            or (str(row.Sector) in {"Unknown", "ETF"})
        )
        for row in df.itertuples(index=False)
    ]
    min_values = np.where(df["Market"].eq("US"), cfg.us_min_median_value, cfg.kr_min_median_value)
    df["LiquidityOK"] = ((df["MedianDailyValue60D"] >= min_values) & (df["CurrentPrice"] >= cfg.min_price)).astype(int)
    if variant.use_flow_filter:
        df["FlowAligned"] = ((df["CountryAligned"] == 1) & (df["SectorAligned"] == 1)).astype(int)
    else:
        df["FlowAligned"] = 1
    eligible = df[(df["TrendOK"] == 1) & (df["LiquidityOK"] == 1) & (df["MomentumScore"] > 0) & (df["FlowAligned"] == 1)].copy()
    eligible = eligible.sort_values(["MomentumScore", "FlowScore", "Symbol"], ascending=[False, False, True]).reset_index(drop=True)
    broad_eligible = df[(df["TrendOK"] == 1) & (df["LiquidityOK"] == 1) & (df["MomentumScore"] > 0)].copy()
    broad_eligible = broad_eligible.sort_values(["MomentumScore", "FlowScore", "Symbol"], ascending=[False, False, True]).reset_index(drop=True)
    picked = eligible.head(cfg.trading_book_size)["AssetKey"].tolist()
    if variant.hold_buffer > 0 and not eligible.empty:
        buffer_keys = set(eligible.head(cfg.trading_book_size + variant.hold_buffer)["AssetKey"].tolist())
        survivors = [asset_key for asset_key in prev_hold_keys if asset_key in buffer_keys]
        picked = list(dict.fromkeys(picked + survivors))
    market_counts: dict[str, int] = {}
    sector_counts: dict[tuple[str, str], int] = {}
    final_picks: list[str] = []
    eligible_by_key = {row.AssetKey: row for row in eligible.itertuples(index=False)}
    for asset_key in picked:
        row = eligible_by_key.get(asset_key)
        if row is None:
            continue
        if market_counts.get(str(row.Market), 0) >= cfg.trading_book_market_cap:
            continue
        sector_key = (str(row.Market), str(row.Sector))
        if variant.max_positions_per_sector is not None and sector_counts.get(sector_key, 0) >= int(variant.max_positions_per_sector):
            continue
        final_picks.append(asset_key)
        market_counts[str(row.Market)] = market_counts.get(str(row.Market), 0) + 1
        sector_counts[sector_key] = sector_counts.get(sector_key, 0) + 1
        if len(final_picks) >= cfg.trading_book_size + variant.hold_buffer:
            break
    if len(final_picks) < cfg.trading_book_size:
        for row in eligible.itertuples(index=False):
            if row.AssetKey in set(final_picks):
                continue
            if market_counts.get(str(row.Market), 0) >= cfg.trading_book_market_cap:
                continue
            sector_key = (str(row.Market), str(row.Sector))
            if variant.max_positions_per_sector is not None and sector_counts.get(sector_key, 0) >= int(variant.max_positions_per_sector):
                continue
            final_picks.append(row.AssetKey)
            market_counts[str(row.Market)] = market_counts.get(str(row.Market), 0) + 1
            sector_counts[sector_key] = sector_counts.get(sector_key, 0) + 1
            if len(final_picks) >= cfg.trading_book_size:
                break
    if variant.min_holdings > 0 and len(final_picks) < variant.min_holdings:
        for row in broad_eligible.itertuples(index=False):
            if row.AssetKey in set(final_picks):
                continue
            if market_counts.get(str(row.Market), 0) >= cfg.trading_book_market_cap:
                continue
            sector_key = (str(row.Market), str(row.Sector))
            if variant.max_positions_per_sector is not None and sector_counts.get(sector_key, 0) >= int(variant.max_positions_per_sector):
                continue
            final_picks.append(row.AssetKey)
            market_counts[str(row.Market)] = market_counts.get(str(row.Market), 0) + 1
            sector_counts[sector_key] = sector_counts.get(sector_key, 0) + 1
            if len(final_picks) >= variant.min_holdings:
                break
    book = eligible[eligible["AssetKey"].isin(final_picks)].copy()
    if variant.min_holdings > 0 and len(book) < variant.min_holdings:
        broadened = broad_eligible[broad_eligible["AssetKey"].isin(final_picks)].copy()
        if not broadened.empty:
            book = broadened
    if variant.use_mad_weighting:
        book["TargetWeight"] = _normalize_target_weight(book, cap=cfg.trading_book_weight_cap)
    elif not book.empty:
        book["TargetWeight"] = 1.0 / len(book)
    else:
        book["TargetWeight"] = pd.Series(dtype=float)
    if (
        not book.empty
        and variant.soft_max_r1m is not None
        and variant.soft_r1m_penalty < 1.0
        and "R1M" in book.columns
    ):
        raw_weights = book["TargetWeight"].copy()
        penalty_mask = book["R1M"].fillna(0.0) > float(variant.soft_max_r1m)
        raw_weights.loc[penalty_mask] = raw_weights.loc[penalty_mask] * float(variant.soft_r1m_penalty)
        book["TargetWeight"] = _normalize_weight_series(raw_weights)
    if (
        not book.empty
        and variant.entry_soft_max_r1m is not None
        and variant.entry_soft_r1m_penalty < 1.0
        and "R1M" in book.columns
    ):
        raw_weights = book["TargetWeight"].copy()
        penalty_mask = (~book["AssetKey"].isin(prev_hold_keys)) & (
            book["R1M"].fillna(0.0) > float(variant.entry_soft_max_r1m)
        )
        raw_weights.loc[penalty_mask] = raw_weights.loc[penalty_mask] * float(variant.entry_soft_r1m_penalty)
        book["TargetWeight"] = _normalize_weight_series(raw_weights)
    if (
        not book.empty
        and variant.breadth_risk_off_threshold is not None
        and len(book) <= int(variant.breadth_risk_off_threshold)
        and float(variant.breadth_risk_off_exposure) < 1.0
    ):
        book["TargetWeight"] = book["TargetWeight"] * float(variant.breadth_risk_off_exposure)
    if (
        not book.empty
        and variant.sector_risk_off_name is not None
        and variant.sector_risk_off_weight_threshold is not None
        and float(variant.sector_risk_off_exposure) < 1.0
    ):
        sector_weight = float(
            book.loc[book["Sector"].astype(str) == str(variant.sector_risk_off_name), "TargetWeight"].sum()
        )
        if sector_weight >= float(variant.sector_risk_off_weight_threshold):
            book["TargetWeight"] = book["TargetWeight"] * float(variant.sector_risk_off_exposure)
    book["SignalDate"] = flow_snapshot["AsOfDate"].iloc[0] if not flow_snapshot.empty else ""
    book["Variant"] = variant.name
    return book


def _build_tenbagger_watch_for_date(metrics: pd.DataFrame, flow_snapshot: pd.DataFrame, cfg: BacktestConfig) -> pd.DataFrame:
    countries, sectors = _allowed_labels(flow_snapshot, cfg)
    df = metrics[metrics["AssetType"] == "STOCK"].copy()
    df["CountryLabel"] = np.where(df["Market"].eq("US"), "US", "Korea")
    df["CountryAligned"] = df["CountryLabel"].isin(countries).astype(int)
    df["SectorAligned"] = [
        int((row.Sector in sectors.get(str(row.Market), set())) or (str(row.Market) == "KR"))
        for row in df.itertuples(index=False)
    ]
    min_values = np.where(df["Market"].eq("US"), cfg.us_min_median_value, cfg.kr_min_median_value)
    df["LiquidityOK"] = ((df["MedianDailyValue60D"] >= min_values) & (df["CurrentPrice"] >= cfg.min_price)).astype(int)
    df["FlowAligned"] = ((df["CountryAligned"] == 1) & (df["SectorAligned"] == 1)).astype(int)
    df["StructureOK"] = ((df["LiquidityOK"] == 1) & (df["TrendOK"] == 1) & (df["R6M"] > 0) & (df["R12M"] > 0)).astype(int)
    df = df[df["StructureOK"] == 1].copy()
    if df.empty:
        return df
    df["WatchGrade"] = "Watch"
    df.loc[(df["FlowAligned"] == 1), "WatchGrade"] = "Starter"
    df.loc[(df["FlowAligned"] == 1) & (df["RelVolume20D60D"] >= 1.10) & (df["DistanceTo52WHigh"] >= -0.08), "WatchGrade"] = "Add-on"
    df["TenbaggerScore"] = (
        0.35 * df["R6M"].fillna(0.0)
        + 0.35 * df["R12M"].fillna(0.0)
        + 0.15 * df["FlowScore"].fillna(0.0)
        + 0.15 * (df["RelVolume20D60D"].fillna(1.0) - 1.0)
    )
    df = df.sort_values(["TenbaggerScore", "MomentumScore", "Symbol"], ascending=[False, False, True]).head(50).reset_index(drop=True)
    df["SignalDate"] = flow_snapshot["AsOfDate"].iloc[0]
    return df


def _forward_return(monthly_close: pd.DataFrame, asset_key: str, signal_date: pd.Timestamp, months: int) -> float:
    if asset_key not in monthly_close.columns or signal_date not in monthly_close.index:
        return np.nan
    idx = monthly_close.index.get_loc(signal_date)
    if idx + months >= len(monthly_close):
        return np.nan
    start = float(monthly_close.iloc[idx][asset_key])
    end = float(monthly_close.iloc[idx + months][asset_key])
    if start <= 0:
        return np.nan
    return end / start - 1.0


def _benchmark_frame(signal_dates: list[pd.Timestamp], monthly_close: pd.DataFrame, cfg: BacktestConfig) -> pd.DataFrame:
    rows = []
    for idx, signal_date in enumerate(signal_dates[:-1]):
        next_date = signal_dates[idx + 1]
        month_ret = monthly_close.loc[next_date] / monthly_close.loc[signal_date] - 1.0
        spy = float(month_ret.get(_asset_key("US", "ETF", "SPY"), np.nan))
        kospi = float(month_ret.get(_asset_key("KR", "ETF", "069500"), np.nan))
        mix_60_40 = np.nanmean([
            0.6 * spy if pd.notna(spy) else np.nan,
            0.4 * float(month_ret.get(_asset_key("US", "ETF", "IEF"), np.nan)) if pd.notna(month_ret.get(_asset_key("US", "ETF", "IEF"), np.nan)) else np.nan,
        ])
        same_universe = month_ret.mean()
        rows.append(
            {
                "SignalDate": signal_date.strftime("%Y-%m-%d"),
                "NextDate": next_date.strftime("%Y-%m-%d"),
                "SPY": spy,
                "KOSPI200": kospi,
                "US6040": mix_60_40,
                "SameUniverseEW": float(same_universe),
            }
        )
    return pd.DataFrame(rows)


def _compare_against_benchmarks(nav_df: pd.DataFrame, benchmark_df: pd.DataFrame) -> pd.DataFrame:
    strategy = pd.to_numeric(nav_df["NetReturn"], errors="coerce")
    merged = nav_df[["SignalDate", "NextDate"]].copy()
    merged["Strategy"] = strategy.values
    merged = merged.merge(benchmark_df, on=["SignalDate", "NextDate"], how="left")
    rows = []
    for col in ["SPY", "KOSPI200", "US6040", "SameUniverseEW"]:
        bench = pd.to_numeric(merged[col], errors="coerce")
        diff = strategy - bench
        strat_summary = _summarize_returns(strategy, merged["NextDate"])
        bench_summary = _summarize_returns(bench, merged["NextDate"])
        excess_summary = _summarize_returns(diff, merged["NextDate"])
        rows.append(
            {
                "Benchmark": col,
                "StrategyCAGR": strat_summary["CAGR"],
                "BenchmarkCAGR": bench_summary["CAGR"],
                "ExcessCAGR": strat_summary["CAGR"] - bench_summary["CAGR"],
                "StrategyMDD": strat_summary["MDD"],
                "BenchmarkMDD": bench_summary["MDD"],
                "StrategySharpe": strat_summary["Sharpe"],
                "BenchmarkSharpe": bench_summary["Sharpe"],
                "MeanMonthlyExcess": float(diff.mean()),
                "HitRateMonthlyExcess": float((diff > 0).mean()),
                "ExcessFinalNAV": excess_summary["FinalNAV"],
            }
        )
    return pd.DataFrame(rows)


def _walkforward_summary(nav_df: pd.DataFrame, window_months: int = 24, step_months: int = 12) -> pd.DataFrame:
    if nav_df.empty:
        return pd.DataFrame()
    df = nav_df.copy()
    df["NextDate"] = pd.to_datetime(df["NextDate"])
    df["NetReturn"] = pd.to_numeric(df["NetReturn"], errors="coerce")
    rows = []
    start_idx = 0
    while start_idx + window_months <= len(df):
        window = df.iloc[start_idx : start_idx + window_months].copy()
        summary = _summarize_returns(window["NetReturn"], window["NextDate"])
        rows.append(
            {
                "WindowStart": str(window["SignalDate"].iloc[0]),
                "WindowEnd": str(window["NextDate"].iloc[-1].date()),
                "Months": int(len(window)),
                "CAGR": summary["CAGR"],
                "MDD": summary["MDD"],
                "Sharpe": summary["Sharpe"],
                "FinalNAV": summary["FinalNAV"],
            }
        )
        start_idx += step_months
    return pd.DataFrame(rows)


def _weak_period_diagnostics(
    nav_df: pd.DataFrame,
    positions_df: pd.DataFrame,
    market_contrib_df: pd.DataFrame,
    sector_contrib_df: pd.DataFrame,
    symbol_contrib_df: pd.DataFrame,
    walkforward_df: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    empty = pd.DataFrame()
    if nav_df.empty or walkforward_df.empty:
        return {
            "window": empty,
            "monthly": empty,
            "market": empty,
            "sector": empty,
            "symbol": empty,
        }

    worst_window = walkforward_df.sort_values("CAGR").head(1).copy()
    if worst_window.empty:
        return {
            "window": empty,
            "monthly": empty,
            "market": empty,
            "sector": empty,
            "symbol": empty,
        }

    start = str(worst_window.iloc[0]["WindowStart"])
    end = str(worst_window.iloc[0]["WindowEnd"])
    nav_mask = (nav_df["SignalDate"] >= start) & (nav_df["NextDate"] <= end)
    pos_mask = (positions_df["SignalDate"] >= start) & (positions_df["NextDate"] <= end)
    market_mask = (market_contrib_df["SignalDate"] >= start) & (market_contrib_df["NextDate"] <= end)
    sector_mask = (sector_contrib_df["SignalDate"] >= start) & (sector_contrib_df["NextDate"] <= end)
    symbol_mask = (symbol_contrib_df["SignalDate"] >= start) & (symbol_contrib_df["NextDate"] <= end)

    monthly = nav_df[nav_mask].copy()
    if not monthly.empty:
        monthly["LossFlag"] = (pd.to_numeric(monthly["NetReturn"], errors="coerce") < 0).astype(int)

    position_slice = positions_df[pos_mask].copy()
    concentration = pd.DataFrame()
    if not position_slice.empty:
        concentration = (
            position_slice.groupby("SignalDate")
            .agg(
                Holdings=("Symbol", "count"),
                Top1Weight=("TargetWeight", "max"),
                Top3Weight=("TargetWeight", lambda s: float(pd.Series(s).sort_values(ascending=False).head(3).sum())),
                AvgMomentumScore=("MomentumScore", "mean"),
                AvgFlowScore=("FlowScore", "mean"),
            )
            .reset_index()
        )
        monthly = monthly.merge(concentration, on="SignalDate", how="left") if not monthly.empty else concentration

    market = (
        market_contrib_df[market_mask]
        .groupby("Market", as_index=False)
        .agg(
            ContributionSum=("Contribution", "sum"),
            ContributionMean=("Contribution", "mean"),
            Months=("Contribution", "count"),
        )
    )
    if not market.empty:
        market = market.sort_values("ContributionSum")

    sector = (
        sector_contrib_df[sector_mask]
        .groupby(["Market", "Sector"], as_index=False)
        .agg(
            ContributionSum=("Contribution", "sum"),
            ContributionMean=("Contribution", "mean"),
            Months=("Contribution", "count"),
        )
    )
    if not sector.empty:
        sector = sector.sort_values("ContributionSum")

    symbol = (
        symbol_contrib_df[symbol_mask]
        .groupby(["Market", "Sector", "Symbol"], as_index=False)
        .agg(
            ContributionSum=("Contribution", "sum"),
            ContributionMean=("Contribution", "mean"),
            Months=("Contribution", "count"),
        )
    )
    if not symbol.empty:
        symbol = symbol.sort_values("ContributionSum")

    return {
        "window": worst_window,
        "monthly": monthly,
        "market": market,
        "sector": sector,
        "symbol": symbol,
    }


def _cost_sensitivity(nav_df: pd.DataFrame, cost_grid_bps: list[float]) -> pd.DataFrame:
    rows = []
    gross = pd.to_numeric(nav_df["GrossReturn"], errors="coerce")
    turnover = pd.to_numeric(nav_df["Turnover"], errors="coerce")
    dates = pd.to_datetime(nav_df["NextDate"], errors="coerce")
    for cost in cost_grid_bps:
        net = gross - turnover * (cost / 10000.0)
        summary = _summarize_returns(net, dates)
        rows.append(
            {
                "OneWayCostBps": cost,
                "CAGR": summary["CAGR"],
                "MDD": summary["MDD"],
                "Sharpe": summary["Sharpe"],
                "FinalNAV": summary["FinalNAV"],
            }
        )
    return pd.DataFrame(rows)


def _run_trading_backtest_variant(
    universe: pd.DataFrame,
    price_cache: dict[str, pd.DataFrame],
    flow_cache: dict[str, pd.DataFrame],
    monthly_close: pd.DataFrame,
    signal_dates: list[pd.Timestamp],
    cfg: BacktestConfig,
    variant: TradingVariant,
) -> dict[str, pd.DataFrame]:
    book_rows: list[dict] = []
    weight_rows: list[dict] = []
    monthly_nav_rows: list[dict] = []
    market_contrib_rows: list[dict] = []
    sector_contrib_rows: list[dict] = []
    symbol_contrib_rows: list[dict] = []
    prev_weights: pd.Series | None = None
    prev_hold_keys: set[str] = set()
    nav = 1.0

    for idx, signal_date in enumerate(signal_dates[:-1]):
        metrics = _historical_metrics(universe, price_cache, flow_cache, signal_date)
        if metrics.empty:
            continue
        flow_snapshot = _historical_flow_snapshot(metrics, monthly_close, signal_date, cfg)
        if flow_snapshot.empty:
            continue
        trading_book = _build_momentum_candidates_for_date(metrics, flow_snapshot, cfg, variant=variant, prev_hold_keys=prev_hold_keys)
        next_date = signal_dates[idx + 1]
        weights = pd.Series(0.0, index=monthly_close.columns)
        if not trading_book.empty:
            for row in trading_book.itertuples(index=False):
                weights[row.AssetKey] = float(row.TargetWeight)
        turnover = float((weights - (prev_weights if prev_weights is not None else 0.0)).abs().sum())
        next_returns = monthly_close.loc[next_date] / monthly_close.loc[signal_date] - 1.0
        gross = float((weights * next_returns.reindex(weights.index).fillna(0.0)).sum())
        net = gross - turnover * (cfg.one_way_cost_bps / 10000.0)
        nav *= 1.0 + net
        monthly_nav_rows.append(
            {
                "Variant": variant.name,
                "SignalDate": signal_date.strftime("%Y-%m-%d"),
                "NextDate": next_date.strftime("%Y-%m-%d"),
                "GrossReturn": gross,
                "NetReturn": net,
                "Turnover": turnover,
                "NAV": nav,
                "Holdings": int((weights > 0).sum()),
            }
        )
        prev_weights = weights.copy()
        prev_hold_keys = set(trading_book["AssetKey"].tolist()) if not trading_book.empty else set()

        for row in trading_book.itertuples(index=False):
            asset_return = float(next_returns.get(row.AssetKey, np.nan))
            contribution = float(row.TargetWeight * asset_return) if pd.notna(asset_return) else np.nan
            book_rows.append(
                {
                    "Variant": variant.name,
                    "SignalDate": signal_date.strftime("%Y-%m-%d"),
                    "NextDate": next_date.strftime("%Y-%m-%d"),
                    "Market": row.Market,
                    "AssetType": row.AssetType,
                    "Symbol": row.Symbol,
                    "Name": row.Name,
                    "Sector": row.Sector,
                    "MomentumScore": row.MomentumScore,
                    "FlowScore": row.FlowScore,
                    "MAD63": row.MAD63,
                    "TargetWeight": row.TargetWeight,
                    "NextMonthReturn": asset_return,
                    "Contribution": contribution,
                }
            )
            symbol_contrib_rows.append(
                {
                    "Variant": variant.name,
                    "SignalDate": signal_date.strftime("%Y-%m-%d"),
                    "NextDate": next_date.strftime("%Y-%m-%d"),
                    "Market": row.Market,
                    "Sector": row.Sector,
                    "Symbol": row.Symbol,
                    "Contribution": contribution,
                }
            )
        for asset_key, weight in weights[weights > 0].items():
            weight_rows.append(
                {
                    "Variant": variant.name,
                    "SignalDate": signal_date.strftime("%Y-%m-%d"),
                    "AssetKey": asset_key,
                    "TargetWeight": float(weight),
                }
            )

        if not trading_book.empty:
            contrib_frame = pd.DataFrame(book_rows[-len(trading_book) :])
            market_group = contrib_frame.groupby("Market", as_index=False)["Contribution"].sum()
            for row in market_group.itertuples(index=False):
                market_contrib_rows.append(
                    {
                        "Variant": variant.name,
                        "SignalDate": signal_date.strftime("%Y-%m-%d"),
                        "NextDate": next_date.strftime("%Y-%m-%d"),
                        "Market": row.Market,
                        "Contribution": row.Contribution,
                    }
                )
            sector_group = contrib_frame.groupby(["Market", "Sector"], as_index=False)["Contribution"].sum()
            for row in sector_group.itertuples(index=False):
                sector_contrib_rows.append(
                    {
                        "Variant": variant.name,
                        "SignalDate": signal_date.strftime("%Y-%m-%d"),
                        "NextDate": next_date.strftime("%Y-%m-%d"),
                        "Market": row.Market,
                        "Sector": row.Sector,
                        "Contribution": row.Contribution,
                    }
                )

    nav_df = pd.DataFrame(monthly_nav_rows)
    positions_df = pd.DataFrame(book_rows)
    weights_df = pd.DataFrame(weight_rows)
    market_df = pd.DataFrame(market_contrib_rows)
    sector_df = pd.DataFrame(sector_contrib_rows)
    symbol_df = pd.DataFrame(symbol_contrib_rows)
    return {
        "nav": nav_df,
        "positions": positions_df,
        "weights": weights_df,
        "market_contrib": market_df,
        "sector_contrib": sector_df,
        "symbol_contrib": symbol_df,
    }


def run_backtests(output_dir: Path | None = None, config: BacktestConfig | None = None) -> dict[str, pd.DataFrame]:
    cfg = config or BacktestConfig()
    target_dir = output_dir or OUTPUT_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    us_stocks, us_etfs = _load_us_universe()
    kr_universe = _load_kr_universe()
    universe = pd.concat([us_stocks, us_etfs, kr_universe], ignore_index=True)
    price_cache, flow_cache = _build_daily_caches(universe)
    monthly_close = _build_monthly_close_matrix(universe, price_cache)
    signal_dates = _signal_dates(monthly_close, cfg.signal_start)
    variant_lookup = _baseline_variant_map()
    baseline_variant = variant_lookup.get(cfg.baseline_variant, variant_lookup["default"])
    baseline_bt = _run_trading_backtest_variant(universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, baseline_variant)
    nav_df = baseline_bt["nav"].drop(columns=["Variant"], errors="ignore")
    trading_positions = baseline_bt["positions"].drop(columns=["Variant"], errors="ignore")
    weight_df = baseline_bt["weights"].drop(columns=["Variant"], errors="ignore")
    market_contrib_df = baseline_bt["market_contrib"].drop(columns=["Variant"], errors="ignore")
    sector_contrib_df = baseline_bt["sector_contrib"].drop(columns=["Variant"], errors="ignore")
    symbol_contrib_df = baseline_bt["symbol_contrib"].drop(columns=["Variant"], errors="ignore")

    watch_rows: list[dict] = []
    for idx, signal_date in enumerate(signal_dates[:-1]):
        metrics = _historical_metrics(universe, price_cache, flow_cache, signal_date)
        if metrics.empty:
            continue
        flow_snapshot = _historical_flow_snapshot(metrics, monthly_close, signal_date, cfg)
        if flow_snapshot.empty:
            continue
        watchlist = _build_tenbagger_watch_for_date(metrics, flow_snapshot, cfg)
        for row in watchlist.itertuples(index=False):
            watch_rows.append(
                {
                    "SignalDate": signal_date.strftime("%Y-%m-%d"),
                    "Market": row.Market,
                    "Symbol": row.Symbol,
                    "Name": row.Name,
                    "Sector": row.Sector,
                    "WatchGrade": row.WatchGrade,
                    "TenbaggerScore": row.TenbaggerScore,
                    "R3MForward": _forward_return(monthly_close, row.AssetKey, signal_date, 3),
                    "R6MForward": _forward_return(monthly_close, row.AssetKey, signal_date, 6),
                    "R12MForward": _forward_return(monthly_close, row.AssetKey, signal_date, 12),
                }
            )
    watch_df = pd.DataFrame(watch_rows)
    benchmark_df = _benchmark_frame(signal_dates, monthly_close, cfg) if signal_dates else pd.DataFrame()

    if nav_df.empty:
        summary_df = pd.DataFrame(
            [{"CAGR": np.nan, "MDD": np.nan, "Sharpe": np.nan, "FinalNAV": np.nan, "AnnualTurnover": np.nan, "Months": 0}]
        )
    else:
        nav_series = pd.to_numeric(nav_df["NAV"], errors="coerce")
        dates = pd.to_datetime(nav_df["NextDate"])
        years = max((dates.iloc[-1] - dates.iloc[0]).days / 365.25, 1 / 365.25)
        summary_df = pd.DataFrame(
            [
                {
                    "CAGR": float(nav_series.iloc[-1] ** (1.0 / years) - 1.0),
                    "MDD": _max_drawdown(nav_series),
                    "Sharpe": _monthly_sharpe(nav_df["NetReturn"]),
                    "FinalNAV": float(nav_series.iloc[-1]),
                    "AnnualTurnover": float(pd.to_numeric(nav_df["Turnover"], errors="coerce").mean() * 12.0),
                    "Months": int(len(nav_df)),
                }
            ]
        )
    benchmark_compare = _compare_against_benchmarks(nav_df, benchmark_df) if not nav_df.empty and not benchmark_df.empty else pd.DataFrame()
    walkforward_df = _walkforward_summary(nav_df, window_months=24, step_months=12) if not nav_df.empty else pd.DataFrame()
    cost_df = _cost_sensitivity(nav_df, cost_grid_bps=[0.0, 5.0, 10.0, 15.0, 25.0, 35.0]) if not nav_df.empty else pd.DataFrame()
    market_summary = (
        market_contrib_df.groupby("Market", as_index=False)["Contribution"].sum().sort_values("Contribution", ascending=False)
        if not market_contrib_df.empty
        else pd.DataFrame()
    )
    sector_summary = (
        sector_contrib_df.groupby(["Market", "Sector"], as_index=False)["Contribution"].sum().sort_values("Contribution", ascending=False)
        if not sector_contrib_df.empty
        else pd.DataFrame()
    )
    symbol_summary = (
        symbol_contrib_df.groupby(["Market", "Sector", "Symbol"], as_index=False)["Contribution"].sum().sort_values("Contribution", ascending=False)
        if not symbol_contrib_df.empty
        else pd.DataFrame()
    )
    weak_diag = _weak_period_diagnostics(
        nav_df=nav_df,
        positions_df=trading_positions,
        market_contrib_df=market_contrib_df,
        sector_contrib_df=sector_contrib_df,
        symbol_contrib_df=symbol_contrib_df,
        walkforward_df=walkforward_df,
    )
    weak_period_symbol_summary = weak_diag["symbol"]
    weak_blacklist = tuple(weak_period_symbol_summary.head(8)["Symbol"].astype(str).tolist()) if not weak_period_symbol_summary.empty else ()

    ablation_rows = []
    for variant in _variant_specs():
        result = _run_trading_backtest_variant(universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, variant)
        nav_variant = result["nav"]
        if nav_variant.empty:
            continue
        summary = _summarize_returns(nav_variant["NetReturn"], nav_variant["NextDate"])
        ablation_rows.append(
            {
                "Variant": variant.name,
                "CAGR": summary["CAGR"],
                "MDD": summary["MDD"],
                "Sharpe": summary["Sharpe"],
                "FinalNAV": summary["FinalNAV"],
                "AnnualTurnover": float(pd.to_numeric(nav_variant["Turnover"], errors="coerce").mean() * 12.0),
                "Months": int(len(nav_variant)),
            }
        )
    ablation_df = pd.DataFrame(ablation_rows).sort_values("CAGR", ascending=False) if ablation_rows else pd.DataFrame()
    refinement_specs = [
        TradingVariant(name="promoted_buffer4", use_flow_filter=True, use_sector_filter=False, use_mad_weighting=True, hold_buffer=4),
        TradingVariant(name="promoted_pruned8", use_flow_filter=True, use_sector_filter=False, use_mad_weighting=True, blacklist_symbols=weak_blacklist),
        TradingVariant(
            name="promoted_buffer4_pruned8",
            use_flow_filter=True,
            use_sector_filter=False,
            use_mad_weighting=True,
            hold_buffer=4,
            blacklist_symbols=weak_blacklist,
        ),
        TradingVariant(
            name="equal_weight_no_mad_min4",
            use_flow_filter=True,
            use_sector_filter=True,
            use_mad_weighting=False,
            min_holdings=4,
        ),
        TradingVariant(
            name="rule_kr_unknown_off",
            use_flow_filter=True,
            use_sector_filter=False,
            use_mad_weighting=True,
            exclude_kr_unknown_stocks=True,
        ),
        TradingVariant(
            name="rule_us_flow_cap",
            use_flow_filter=True,
            use_sector_filter=False,
            use_mad_weighting=True,
            us_flow_score_cap=0.30,
        ),
        TradingVariant(
            name="rule_combo_generalized",
            use_flow_filter=True,
            use_sector_filter=False,
            use_mad_weighting=True,
            exclude_kr_unknown_stocks=True,
            us_flow_score_cap=0.30,
        ),
        TradingVariant(
            name="rule_trend_chase_cap",
            use_flow_filter=True,
            use_sector_filter=True,
            use_mad_weighting=False,
            min_holdings=4,
            max_r1m=0.20,
        ),
        TradingVariant(
            name="rule_trend_chase_soft",
            use_flow_filter=True,
            use_sector_filter=True,
            use_mad_weighting=False,
            min_holdings=4,
            soft_max_r1m=0.20,
            soft_r1m_penalty=0.5,
        ),
        TradingVariant(
            name="rule_trend_chase_entry_soft",
            use_flow_filter=True,
            use_sector_filter=True,
            use_mad_weighting=False,
            min_holdings=4,
            entry_soft_max_r1m=0.20,
            entry_soft_r1m_penalty=0.5,
        ),
        TradingVariant(
            name="rule_sector_cap2",
            use_flow_filter=True,
            use_sector_filter=True,
            use_mad_weighting=False,
            min_holdings=4,
            max_positions_per_sector=2,
        ),
        TradingVariant(
            name="rule_breadth_risk_off",
            use_flow_filter=True,
            use_sector_filter=True,
            use_mad_weighting=False,
            min_holdings=4,
            breadth_risk_off_threshold=4,
            breadth_risk_off_exposure=0.75,
        ),
        TradingVariant(
            name="rule_breadth_risk_off_080",
            use_flow_filter=True,
            use_sector_filter=True,
            use_mad_weighting=False,
            min_holdings=4,
            breadth_risk_off_threshold=4,
            breadth_risk_off_exposure=0.80,
        ),
        TradingVariant(
            name="rule_breadth_it_risk_off",
            use_flow_filter=True,
            use_sector_filter=True,
            use_mad_weighting=False,
            min_holdings=4,
            breadth_risk_off_threshold=4,
            breadth_risk_off_exposure=0.75,
            sector_risk_off_name="Information Technology",
            sector_risk_off_weight_threshold=0.55,
            sector_risk_off_exposure=0.80,
        ),
        TradingVariant(
            name="rule_sector_cap2_breadth_risk_off",
            use_flow_filter=True,
            use_sector_filter=True,
            use_mad_weighting=False,
            min_holdings=4,
            max_positions_per_sector=2,
            breadth_risk_off_threshold=4,
            breadth_risk_off_exposure=0.75,
        ),
        TradingVariant(
            name="rule_sector_cap2_breadth_it_risk_off",
            use_flow_filter=True,
            use_sector_filter=True,
            use_mad_weighting=False,
            min_holdings=4,
            max_positions_per_sector=2,
            breadth_risk_off_threshold=4,
            breadth_risk_off_exposure=0.75,
            sector_risk_off_name="Information Technology",
            sector_risk_off_weight_threshold=0.55,
            sector_risk_off_exposure=0.80,
        ),
    ]
    refinement_rows = []
    for variant in refinement_specs:
        result = _run_trading_backtest_variant(universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, variant)
        nav_variant = result["nav"]
        if nav_variant.empty:
            continue
        summary = _summarize_returns(nav_variant["NetReturn"], nav_variant["NextDate"])
        refinement_rows.append(
            {
                "Variant": variant.name,
                "CAGR": summary["CAGR"],
                "MDD": summary["MDD"],
                "Sharpe": summary["Sharpe"],
                "FinalNAV": summary["FinalNAV"],
                "AnnualTurnover": float(pd.to_numeric(nav_variant["Turnover"], errors="coerce").mean() * 12.0),
                "Months": int(len(nav_variant)),
                "BlacklistSymbols": ",".join(variant.blacklist_symbols),
                "MinHoldings": int(variant.min_holdings),
                "HoldBuffer": int(variant.hold_buffer),
                "ExcludeKRUnknownStocks": int(variant.exclude_kr_unknown_stocks),
                "USFlowScoreCap": "" if variant.us_flow_score_cap is None else float(variant.us_flow_score_cap),
                "MaxR1M": "" if variant.max_r1m is None else float(variant.max_r1m),
                "SoftMaxR1M": "" if variant.soft_max_r1m is None else float(variant.soft_max_r1m),
                "SoftR1MPenalty": float(variant.soft_r1m_penalty),
                "EntrySoftMaxR1M": "" if variant.entry_soft_max_r1m is None else float(variant.entry_soft_max_r1m),
                "EntrySoftR1MPenalty": float(variant.entry_soft_r1m_penalty),
                "MaxPositionsPerSector": "" if variant.max_positions_per_sector is None else int(variant.max_positions_per_sector),
                "BreadthRiskOffThreshold": "" if variant.breadth_risk_off_threshold is None else int(variant.breadth_risk_off_threshold),
                "BreadthRiskOffExposure": float(variant.breadth_risk_off_exposure),
                "SectorRiskOffName": "" if variant.sector_risk_off_name is None else str(variant.sector_risk_off_name),
                "SectorRiskOffWeightThreshold": "" if variant.sector_risk_off_weight_threshold is None else float(variant.sector_risk_off_weight_threshold),
                "SectorRiskOffExposure": float(variant.sector_risk_off_exposure),
                "MinRelVolume": "" if variant.min_rel_volume is None else float(variant.min_rel_volume),
            }
        )
    refinement_df = pd.DataFrame(refinement_rows).sort_values("CAGR", ascending=False) if refinement_rows else pd.DataFrame()

    grade_rows = []
    for (market, grade), group in watch_df.groupby(["Market", "WatchGrade"]):
        row = {
            "Market": market,
            "WatchGrade": grade,
            "Count": int(len(group)),
        }
        for col in ["R3MForward", "R6MForward", "R12MForward"]:
            vals = pd.to_numeric(group[col], errors="coerce").dropna()
            row[f"{col}_Mean"] = float(vals.mean()) if not vals.empty else np.nan
            row[f"{col}_Median"] = float(vals.median()) if not vals.empty else np.nan
            row[f"{col}_HitRate"] = float((vals > 0).mean()) if not vals.empty else np.nan
            row[f"{col}_P90"] = float(vals.quantile(0.9)) if len(vals) >= 2 else np.nan
        grade_rows.append(row)
    grade_summary = pd.DataFrame(grade_rows)

    nav_df.to_csv(target_dir / "trading_book_backtest_nav.csv", index=False, encoding="utf-8-sig")
    trading_positions.to_csv(target_dir / "trading_book_backtest_positions.csv", index=False, encoding="utf-8-sig")
    weight_df.to_csv(target_dir / "trading_book_backtest_weights.csv", index=False, encoding="utf-8-sig")
    summary_df.to_csv(target_dir / "trading_book_backtest_summary.csv", index=False, encoding="utf-8-sig")
    benchmark_df.to_csv(target_dir / "trading_book_benchmark_returns.csv", index=False, encoding="utf-8-sig")
    benchmark_compare.to_csv(target_dir / "trading_book_benchmark_compare.csv", index=False, encoding="utf-8-sig")
    walkforward_df.to_csv(target_dir / "trading_book_walkforward_summary.csv", index=False, encoding="utf-8-sig")
    cost_df.to_csv(target_dir / "trading_book_cost_sensitivity.csv", index=False, encoding="utf-8-sig")
    market_contrib_df.to_csv(target_dir / "trading_book_market_contributions.csv", index=False, encoding="utf-8-sig")
    sector_contrib_df.to_csv(target_dir / "trading_book_sector_contributions.csv", index=False, encoding="utf-8-sig")
    symbol_contrib_df.to_csv(target_dir / "trading_book_symbol_contributions.csv", index=False, encoding="utf-8-sig")
    market_summary.to_csv(target_dir / "trading_book_market_contribution_summary.csv", index=False, encoding="utf-8-sig")
    sector_summary.to_csv(target_dir / "trading_book_sector_contribution_summary.csv", index=False, encoding="utf-8-sig")
    symbol_summary.to_csv(target_dir / "trading_book_symbol_contribution_summary.csv", index=False, encoding="utf-8-sig")
    weak_period_symbol_summary.to_csv(target_dir / "trading_book_weak_period_symbol_summary.csv", index=False, encoding="utf-8-sig")
    weak_diag["window"].to_csv(target_dir / "trading_book_weak_period_window.csv", index=False, encoding="utf-8-sig")
    weak_diag["monthly"].to_csv(target_dir / "trading_book_weak_period_monthly_diagnostics.csv", index=False, encoding="utf-8-sig")
    weak_diag["market"].to_csv(target_dir / "trading_book_weak_period_market_summary.csv", index=False, encoding="utf-8-sig")
    weak_diag["sector"].to_csv(target_dir / "trading_book_weak_period_sector_summary.csv", index=False, encoding="utf-8-sig")
    ablation_df.to_csv(target_dir / "trading_book_ablation_compare.csv", index=False, encoding="utf-8-sig")
    refinement_df.to_csv(target_dir / "trading_book_refinement_compare.csv", index=False, encoding="utf-8-sig")
    watch_df.to_csv(target_dir / "tenbagger_backtest_occurrences.csv", index=False, encoding="utf-8-sig")
    grade_summary.to_csv(target_dir / "tenbagger_backtest_grade_summary.csv", index=False, encoding="utf-8-sig")

    summary_json = {
        "baseline_variant": baseline_variant.name,
        "trading_book": summary_df.iloc[0].to_dict() if not summary_df.empty else {},
        "benchmarks": int(len(benchmark_compare)),
        "walkforward_rows": int(len(walkforward_df)),
        "weak_period_start": "" if weak_diag["window"].empty else str(weak_diag["window"].iloc[0]["WindowStart"]),
        "weak_period_end": "" if weak_diag["window"].empty else str(weak_diag["window"].iloc[0]["WindowEnd"]),
        "ablation_rows": int(len(ablation_df)),
        "refinement_rows": int(len(refinement_df)),
        "tenbagger_grade_rows": int(len(grade_summary)),
        "occurrences": int(len(watch_df)),
    }
    (target_dir / "split_models_backtest_summary.json").write_text(json.dumps(summary_json, indent=2), encoding="utf-8")

    return {
        "trading_book_backtest_nav": nav_df,
        "trading_book_backtest_positions": trading_positions,
        "trading_book_backtest_summary": summary_df,
        "trading_book_benchmark_returns": benchmark_df,
        "trading_book_benchmark_compare": benchmark_compare,
        "trading_book_walkforward_summary": walkforward_df,
        "trading_book_cost_sensitivity": cost_df,
        "trading_book_market_contribution_summary": market_summary,
        "trading_book_sector_contribution_summary": sector_summary,
        "trading_book_symbol_contribution_summary": symbol_summary,
        "trading_book_weak_period_symbol_summary": weak_period_symbol_summary,
        "trading_book_weak_period_window": weak_diag["window"],
        "trading_book_weak_period_monthly_diagnostics": weak_diag["monthly"],
        "trading_book_weak_period_market_summary": weak_diag["market"],
        "trading_book_weak_period_sector_summary": weak_diag["sector"],
        "trading_book_ablation_compare": ablation_df,
        "trading_book_refinement_compare": refinement_df,
        "tenbagger_backtest_occurrences": watch_df,
        "tenbagger_backtest_grade_summary": grade_summary,
    }
