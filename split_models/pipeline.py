from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output" / "split_models"
GLOBAL_OBSERVER_BUILD = ROOT / "global_flow_observer" / "scripts" / "build_observer_state.py"
GLOBAL_OBSERVER_OUTPUT = ROOT / "global_flow_observer" / "outputs"
KR_METADATA_CACHE = ROOT / "data" / "kr_metadata" / "kr_symbol_metadata.csv"
KR_METADATA_OVERRIDES = ROOT / "inputs" / "kr_metadata_overrides.csv"


@dataclass(frozen=True)
class PipelineConfig:
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


@dataclass(frozen=True)
class KRDataContext:
    universe_path: Path
    price_root: Path
    flow_root: Path | None
    source_label: str


def _ensure_observer_outputs() -> None:
    required = [
        GLOBAL_OBSERVER_OUTPUT / "current_regime_summary.csv",
        GLOBAL_OBSERVER_OUTPUT / "asset_leadership_table.csv",
        GLOBAL_OBSERVER_OUTPUT / "equity_region_rotation.csv",
        GLOBAL_OBSERVER_OUTPUT / "real_assets_vs_financial_assets.csv",
        GLOBAL_OBSERVER_OUTPUT / "risk_vs_defense.csv",
    ]
    if all(path.exists() for path in required):
        return
    subprocess.run([sys.executable, str(GLOBAL_OBSERVER_BUILD)], cwd=ROOT, check=True)


def _read_price_frame(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, compression="gzip", parse_dates=["date"])
    df = df.rename(columns=str.lower).copy()
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0.0)
    df = df.dropna(subset=["date", "close"])
    df = df[df["close"] > 0].sort_values("date").drop_duplicates(subset=["date"]).reset_index(drop=True)
    return df


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


def _load_us_listing() -> pd.DataFrame:
    universe = pd.read_csv(ROOT / "backtests" / "us_stock_sp100_universe_pitwiki.csv")
    universe = universe[universe["Status"].astype(str).eq("OK")].copy()
    universe["Symbol"] = universe["Symbol"].astype(str)
    return universe[["Symbol", "Name", "Sector"]].drop_duplicates("Symbol").reset_index(drop=True)


def _discover_kr_data_context() -> KRDataContext:
    universe_candidates = [
        ROOT / "backtests" / "kis_operating_universe_candidates_institutional_v1.csv",
        ROOT / "backtests" / "kis_operating_universe_candidates.csv",
    ]
    price_roots = [
        ROOT / "data" / "prices_operating_institutional_v1",
        ROOT / "data" / "prices_operating_v2",
        ROOT / "data" / "prices_operating",
        ROOT / "data" / "prices",
    ]
    flow_roots = [
        ROOT / "data" / "flows_operating_institutional_v1",
        ROOT / "data" / "flows_kis_8y",
        ROOT / "data" / "flows_kis",
        ROOT / "data" / "flows_naver_8y",
        ROOT / "data" / "flows_test",
    ]

    universe_path = next((path for path in universe_candidates if path.exists()), universe_candidates[0])
    price_root = next(
        (path for path in price_roots if (path / "stock").exists() and (path / "etf").exists()),
        price_roots[0],
    )
    flow_root = next((path for path in flow_roots if (path / "stock").exists()), None)

    source_parts = []
    if "institutional_v1" in price_root.name:
        source_parts.append("KIS_OPERATING_INSTITUTIONAL_V1")
    elif "operating" in price_root.name:
        source_parts.append("KIS_OPERATING")
    else:
        source_parts.append("KIS_PRICE_ARCHIVE")
    if flow_root is not None:
        if "operating_institutional_v1" in flow_root.name:
            source_parts.append("OPERATING_FLOW_CACHE")
        else:
            source_parts.append(flow_root.name.upper())

    return KRDataContext(
        universe_path=universe_path,
        price_root=price_root,
        flow_root=flow_root,
        source_label="+".join(source_parts),
    )


def _load_kr_listing(codes: list[str], etf_codes: list[str]) -> pd.DataFrame:
    rows = []
    wanted = {*(str(code).zfill(6) for code in codes), *(str(code).zfill(6) for code in etf_codes)}

    if KR_METADATA_CACHE.exists():
        cached = pd.read_csv(KR_METADATA_CACHE)
        cached["Symbol"] = cached["Symbol"].astype(str).str.zfill(6)
        rows.append(cached[["Symbol", "Name", "Sector", "Market"]].copy())

    try:
        from pykrx import stock

        stock_rows = []
        for code in codes:
            code = str(code).zfill(6)
            try:
                name = stock.get_market_ticker_name(code)
            except Exception:
                name = code
            stock_rows.append({"Symbol": code, "Name": name or code, "Sector": "Unknown", "Market": "STOCK"})
        rows.append(pd.DataFrame(stock_rows))
    except Exception:
        pass

    if KR_METADATA_OVERRIDES.exists():
        overrides = pd.read_csv(KR_METADATA_OVERRIDES)
        overrides["Symbol"] = overrides["Symbol"].astype(str).str.zfill(6)
        rows.append(overrides[["Symbol", "Name", "Sector", "Market"]].copy())

    if rows:
        listing = pd.concat(rows, ignore_index=True)
        listing["Symbol"] = listing["Symbol"].astype(str).str.zfill(6)
        listing["Name"] = listing["Name"].fillna(listing["Symbol"]).astype(str)
        listing["Sector"] = listing["Sector"].fillna("Unknown").astype(str)
        listing["Market"] = listing["Market"].fillna("STOCK").astype(str)
        listing = listing[listing["Symbol"].isin(wanted)].copy()
        listing = listing.sort_values(["Symbol", "Market"]).drop_duplicates(subset=["Symbol", "Market"], keep="last")
        if not listing.empty:
            return listing.reset_index(drop=True)

    fallback = [{"Symbol": code, "Name": code, "Sector": "Unknown", "Market": "STOCK"} for code in codes]
    fallback += [{"Symbol": code, "Name": code, "Sector": "ETF", "Market": "ETF"} for code in etf_codes]
    return pd.DataFrame(fallback)


def _compute_metrics(
    symbol: str,
    market: str,
    asset_type: str,
    sector: str,
    name: str,
    price_path: Path,
    flow_path: Path | None = None,
) -> dict | None:
    if not price_path.exists():
        return None
    px = _read_price_frame(price_path)
    if len(px) < 252:
        return None
    close = px["close"]
    value = px["close"] * px["volume"]
    ma50 = close.tail(50).mean()
    ma200 = close.tail(200).mean()
    current = float(close.iloc[-1])
    median_value_60 = float(value.tail(60).median()) if len(value) >= 60 else np.nan
    avg_value_20 = float(value.tail(20).mean()) if len(value) >= 20 else np.nan
    avg_volume_20 = float(px["volume"].tail(20).mean()) if len(px) >= 20 else np.nan
    avg_volume_60 = float(px["volume"].tail(60).mean()) if len(px) >= 60 else np.nan
    rel_volume = avg_volume_20 / avg_volume_60 if avg_volume_60 and avg_volume_60 > 0 else np.nan
    high_252 = float(close.tail(252).max())
    dist_to_high = current / high_252 - 1.0 if high_252 > 0 else np.nan
    r1m = _safe_return(close, 21)
    r3m = _safe_return(close, 63)
    r6m = _safe_return(close, 126)
    r12m = _safe_return(close, 252)
    trend_ok = int(current > ma50 and ma50 > ma200)
    mad_63 = _rolling_mad(close, window=63)

    flow_score = np.nan
    flow_accel = np.nan
    if market == "KR" and flow_path is not None and flow_path.exists():
        flow = pd.read_csv(flow_path, compression="gzip", parse_dates=["date"]).sort_values("date")
        merged = px.merge(flow, on="date", how="inner")
        if len(merged) >= 60:
            traded_value = (merged["close"] * merged["volume"]).replace(0.0, np.nan)
            foreign_notional = merged["foreign_net_volume"] * merged["close"]
            inst_notional = merged["institution_net_volume"] * merged["close"]
            foreign_20 = float(foreign_notional.tail(20).sum() / traded_value.tail(20).sum()) if traded_value.tail(20).sum() else np.nan
            inst_20 = float(inst_notional.tail(20).sum() / traded_value.tail(20).sum()) if traded_value.tail(20).sum() else np.nan
            foreign_ratio_delta = float(merged["foreign_ratio"].iloc[-1] - merged["foreign_ratio"].iloc[-21]) if len(merged) > 21 else np.nan
            flow_score = np.nanmean([foreign_20, 0.5 * inst_20, 0.1 * foreign_ratio_delta])
            flow_accel = foreign_ratio_delta
    elif market == "US":
        vol_bonus = max((rel_volume or np.nan) - 1.0, 0.0) if pd.notna(rel_volume) else np.nan
        price_expansion = np.nanmean([r3m, r6m])
        breakout_bonus = 1.0 + dist_to_high if pd.notna(dist_to_high) else np.nan
        flow_score = np.nanmean([price_expansion, vol_bonus, breakout_bonus - 1.0 if pd.notna(breakout_bonus) else np.nan])
        flow_accel = vol_bonus

    momentum_score = np.nanmean([0.20 * r1m, 0.30 * r3m, 0.30 * r6m, 0.20 * r12m])
    return {
        "AsOfDate": px["date"].iloc[-1].strftime("%Y-%m-%d"),
        "Market": market,
        "AssetType": asset_type,
        "Symbol": symbol,
        "Name": name,
        "Sector": sector,
        "CurrentPrice": current,
        "MedianDailyValue60D": median_value_60,
        "AvgDailyValue20D": avg_value_20,
        "RelVolume20D60D": rel_volume,
        "R1M": r1m,
        "R3M": r3m,
        "R6M": r6m,
        "R12M": r12m,
        "MA50": ma50,
        "MA200": ma200,
        "TrendOK": trend_ok,
        "MAD63": mad_63,
        "DistanceTo52WHigh": dist_to_high,
        "FlowScore": flow_score,
        "FlowAcceleration": flow_accel,
        "MomentumScore": momentum_score,
    }


def _load_us_stock_metrics() -> pd.DataFrame:
    listing = _load_us_listing()
    rows: list[dict] = []
    for row in listing.itertuples(index=False):
        item = _compute_metrics(
            symbol=row.Symbol,
            market="US",
            asset_type="STOCK",
            sector=str(row.Sector or "Unknown"),
            name=str(row.Name),
            price_path=ROOT / "data" / "prices_us_stock_sp100_pitwiki" / "stock" / f"{row.Symbol}.csv.gz",
        )
        if item is not None:
            rows.append(item)
    return pd.DataFrame(rows)


def _load_us_etf_metrics() -> pd.DataFrame:
    universe = pd.read_csv(ROOT / "backtests" / "us_etf_core_universe.csv")
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
    rows: list[dict] = []
    for row in universe.itertuples(index=False):
        item = _compute_metrics(
            symbol=row.Ticker,
            market="US",
            asset_type="ETF",
            sector=sector_map.get(row.Ticker, "ETF"),
            name=str(row.Name),
            price_path=ROOT / "data" / "prices_us_etf_core" / "etf" / f"{row.Ticker}.csv.gz",
        )
        if item is not None:
            rows.append(item)
    return pd.DataFrame(rows)


def _load_kr_metrics(context: KRDataContext) -> pd.DataFrame:
    universe = pd.read_csv(context.universe_path)
    universe["Code"] = universe["Code"].astype(str).str.zfill(6)
    stock_codes = universe[universe["Market"].astype(str).eq("STOCK")]["Code"].tolist()
    etf_codes = universe[universe["Market"].astype(str).eq("ETF")]["Code"].tolist()
    listing = _load_kr_listing(stock_codes, etf_codes)
    rows: list[dict] = []
    for row in universe.itertuples(index=False):
        code = str(row.Code).zfill(6)
        asset_type = str(row.Market)
        meta = listing[(listing["Symbol"] == code) & (listing["Market"] == asset_type)]
        if meta.empty:
            meta = listing[listing["Symbol"] == code]
        name = str(meta.iloc[0]["Name"]) if not meta.empty else code
        sector = str(meta.iloc[0]["Sector"]) if not meta.empty else ("ETF" if asset_type == "ETF" else "Unknown")
        subdir = "etf" if asset_type == "ETF" else "stock"
        flow_path = (context.flow_root / "stock" / f"{code}.csv.gz") if (asset_type == "STOCK" and context.flow_root) else None
        item = _compute_metrics(
            symbol=code,
            market="KR",
            asset_type=asset_type,
            sector=sector,
            name=name,
            price_path=context.price_root / subdir / f"{code}.csv.gz",
            flow_path=flow_path,
        )
        if item is not None:
            item["KRPriceSource"] = str(context.price_root)
            item["KRFlowSource"] = str(context.flow_root) if context.flow_root is not None else ""
            item["KRUniverseSource"] = str(context.universe_path)
            rows.append(item)
    return pd.DataFrame(rows)


def _latest_date_from_gzip_csv(path: Path) -> pd.Timestamp | pd.NaT:
    if not path.exists():
        return pd.NaT
    try:
        df = pd.read_csv(path, compression="gzip", usecols=["date"], parse_dates=["date"])
    except Exception:
        return pd.NaT
    if df.empty:
        return pd.NaT
    return pd.to_datetime(df["date"], errors="coerce").dropna().max()


def _recent_business_day() -> pd.Timestamp:
    dt = pd.Timestamp(datetime.today().date())
    while dt.weekday() >= 5:
        dt -= pd.Timedelta(days=1)
    return dt


def _build_data_readiness(kr_context: KRDataContext) -> pd.DataFrame:
    universe = pd.read_csv(kr_context.universe_path)
    universe["Code"] = universe["Code"].astype(str).str.zfill(6)
    expected_day = _recent_business_day()
    stale_cutoff = expected_day - pd.Timedelta(days=7)
    rows: list[dict] = []

    for asset_type, subdir in [("STOCK", "stock"), ("ETF", "etf")]:
        codes = sorted(universe[universe["Market"].astype(str).eq(asset_type)]["Code"].unique().tolist())
        if not codes:
            continue
        price_dates = []
        price_missing = 0
        price_stale = 0
        for code in codes:
            latest = _latest_date_from_gzip_csv(kr_context.price_root / subdir / f"{code}.csv.gz")
            if pd.isna(latest):
                price_missing += 1
                continue
            price_dates.append(latest)
            if latest.normalize() < stale_cutoff:
                price_stale += 1

        flow_expected = codes if asset_type == "STOCK" and kr_context.flow_root is not None else []
        flow_dates = []
        flow_missing = 0
        flow_stale = 0
        for code in flow_expected:
            latest = _latest_date_from_gzip_csv(kr_context.flow_root / "stock" / f"{code}.csv.gz")
            if pd.isna(latest):
                flow_missing += 1
                continue
            flow_dates.append(latest)
            if latest.normalize() < stale_cutoff:
                flow_stale += 1

        rows.append(
            {
                "Scope": f"KR_{asset_type}",
                "ExpectedCount": len(codes),
                "PriceRoot": str(kr_context.price_root / subdir),
                "PriceFilesPresent": len(price_dates),
                "PriceMissingCount": price_missing,
                "PriceStaleOver7DCount": price_stale,
                "PriceLatestMinDate": min(price_dates).strftime("%Y-%m-%d") if price_dates else "",
                "PriceLatestMaxDate": max(price_dates).strftime("%Y-%m-%d") if price_dates else "",
                "FlowRoot": str(kr_context.flow_root / "stock") if flow_expected else "",
                "FlowFilesPresent": len(flow_dates),
                "FlowMissingCount": flow_missing,
                "FlowStaleOver7DCount": flow_stale,
                "FlowLatestMinDate": min(flow_dates).strftime("%Y-%m-%d") if flow_dates else "",
                "FlowLatestMaxDate": max(flow_dates).strftime("%Y-%m-%d") if flow_dates else "",
                "ExpectedBusinessDate": expected_day.strftime("%Y-%m-%d"),
            }
        )

    return pd.DataFrame(rows)


def _top_sector_scores(metrics: pd.DataFrame, market: str, top_n: int) -> pd.DataFrame:
    subset = metrics[(metrics["Market"] == market) & metrics["Sector"].notna()].copy()
    if subset.empty:
        return pd.DataFrame(columns=["Market", "Label", "Score", "Rank"])
    subset["Sector"] = subset["Sector"].astype(str).replace({"": "Unknown", "nan": "Unknown"}).fillna("Unknown")
    known = subset[~subset["Sector"].isin(["Unknown"])].copy()
    if known.empty:
        synthetic_score = float(subset["MomentumScore"].median()) + 0.5 * float(subset["FlowScore"].median())
        return pd.DataFrame(
            [
                {
                    "Market": market,
                    "Label": f"{market}_LEADERS",
                    "Score": synthetic_score,
                    "Rank": 1,
                }
            ]
        )
    grouped = (
        known.groupby("Sector")
        .agg(
            MomentumScore=("MomentumScore", "median"),
            FlowScore=("FlowScore", "median"),
            Count=("Symbol", "count"),
        )
        .reset_index()
    )
    grouped["Score"] = grouped["MomentumScore"].fillna(0.0) + 0.5 * grouped["FlowScore"].fillna(0.0) + 0.01 * grouped["Count"]
    grouped = grouped.sort_values(["Score", "Sector"], ascending=[False, True]).reset_index(drop=True)
    grouped["Rank"] = range(1, len(grouped) + 1)
    grouped["Market"] = market
    grouped["Label"] = grouped["Sector"]
    return grouped.head(top_n)[["Market", "Label", "Score", "Rank"]]


def _build_flow_regime_snapshot(
    us_stock_metrics: pd.DataFrame,
    us_etf_metrics: pd.DataFrame,
    kr_metrics: pd.DataFrame,
    config: PipelineConfig,
) -> pd.DataFrame:
    _ensure_observer_outputs()
    regime = pd.read_csv(GLOBAL_OBSERVER_OUTPUT / "current_regime_summary.csv").iloc[0]
    risk = pd.read_csv(GLOBAL_OBSERVER_OUTPUT / "risk_vs_defense.csv").iloc[0]
    equity = pd.read_csv(GLOBAL_OBSERVER_OUTPUT / "equity_region_rotation.csv")

    country_rows = []
    scores = {
        "US": float(equity[equity["Ticker"] == "SPY"]["R3M"].iloc[0]),
        "Developed ex-US": float(equity[equity["Ticker"] == "EFA"]["R3M"].iloc[0]),
        "Emerging": float(equity[equity["Ticker"] == "EEM"]["R3M"].iloc[0]),
    }
    korea_proxy = kr_metrics[(kr_metrics["AssetType"] == "ETF") & (kr_metrics["Symbol"] == "069500")]
    if korea_proxy.empty:
        korea_score = float(kr_metrics[kr_metrics["AssetType"] == "STOCK"]["MomentumScore"].median())
    else:
        korea_score = float(korea_proxy.iloc[0]["R3M"])
    scores["Korea"] = korea_score
    ranked_countries = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    for rank, (label, score) in enumerate(ranked_countries, start=1):
        country_rows.append(
            {
                "AsOfDate": str(regime["SignalDate"]),
                "ScopeType": "COUNTRY",
                "Market": "GLOBAL",
                "Label": label,
                "FlowScore": score,
                "Rank": rank,
                "Regime": str(regime["Regime"]),
                "RiskState": "RISK_POSITIVE" if float(risk["Spread3M"]) > 0 else "DEFENSE_POSITIVE",
                "AggressiveAllowed": int(str(regime["Regime"]) != "Risk-Off" and float(risk["Spread3M"]) > -0.02),
                "Source": "global_observer_plus_kr_proxy",
            }
        )

    sector_rows = []
    for sector_scores in [
        _top_sector_scores(us_stock_metrics, market="US", top_n=config.top_sector_count),
        _top_sector_scores(kr_metrics[kr_metrics["AssetType"] == "STOCK"], market="KR", top_n=config.top_sector_count),
    ]:
        for row in sector_scores.itertuples(index=False):
            sector_rows.append(
                {
                    "AsOfDate": str(regime["SignalDate"]),
                    "ScopeType": "SECTOR",
                    "Market": row.Market,
                    "Label": row.Label,
                    "FlowScore": row.Score,
                    "Rank": row.Rank,
                    "Regime": str(regime["Regime"]),
                    "RiskState": "RISK_POSITIVE" if float(risk["Spread3M"]) > 0 else "DEFENSE_POSITIVE",
                    "AggressiveAllowed": int(str(regime["Regime"]) != "Risk-Off" and float(risk["Spread3M"]) > -0.02),
                    "Source": "cross_sectional_sector_strength",
                }
            )

    out = pd.DataFrame(country_rows + sector_rows)
    out = out.sort_values(["ScopeType", "Rank", "Market", "Label"]).reset_index(drop=True)
    return out


def _allowed_labels(flow_snapshot: pd.DataFrame, config: PipelineConfig) -> tuple[set[str], dict[str, set[str]]]:
    countries = set(
        flow_snapshot[flow_snapshot["ScopeType"].eq("COUNTRY")]
        .sort_values("Rank")
        .head(config.top_country_count)["Label"]
        .tolist()
    )
    sectors: dict[str, set[str]] = {}
    sector_snapshot = flow_snapshot[flow_snapshot["ScopeType"].eq("SECTOR")].copy()
    for market, group in sector_snapshot.groupby("Market"):
        sectors[market] = set(group.sort_values("Rank").head(config.top_sector_count)["Label"].tolist())
    return countries, sectors


def _normalize_target_weight(df: pd.DataFrame, cap: float) -> pd.Series:
    if df.empty:
        return pd.Series(dtype=float)
    inv_mad = 1.0 / df["MAD63"].clip(lower=1e-6).fillna(df["MAD63"].median())
    weights = inv_mad / inv_mad.sum()
    effective_cap = max(cap, 1.0 / len(df))
    weights = weights.clip(upper=effective_cap)
    if weights.sum() <= 0:
        return pd.Series(np.repeat(0.0, len(df)), index=df.index)
    return weights / weights.sum()


def _build_momentum_trade_candidates(
    metrics: pd.DataFrame,
    flow_snapshot: pd.DataFrame,
    config: PipelineConfig,
) -> pd.DataFrame:
    allowed_countries, allowed_sectors = _allowed_labels(flow_snapshot, config)
    df = metrics.copy()
    country_label = np.where(df["Market"].eq("US"), "US", "Korea")
    sector_ok = [
        (row.Sector in allowed_sectors.get(str(row.Market), set())) if str(row.Sector) not in {"Unknown", "ETF"} else True
        for row in df.itertuples(index=False)
    ]
    df["CountryLabel"] = country_label
    df["CountryAligned"] = df["CountryLabel"].isin(allowed_countries).astype(int)
    df["SectorAligned"] = pd.Series(sector_ok, index=df.index).astype(int)
    min_values = np.where(df["Market"].eq("US"), config.us_min_median_value, config.kr_min_median_value)
    df["LiquidityOK"] = ((df["MedianDailyValue60D"] >= min_values) & (df["CurrentPrice"] >= config.min_price)).astype(int)
    df["FlowAligned"] = ((df["CountryAligned"] == 1) & ((df["SectorAligned"] == 1) | df["AssetType"].isin(["ETF"]))).astype(int)
    df = df.sort_values(["MomentumScore", "FlowScore", "Symbol"], ascending=[False, False, True]).reset_index(drop=True)
    df["MomentumRank"] = range(1, len(df) + 1)
    df["CandidateState"] = "EXCLUDE"

    eligible = df[(df["TrendOK"] == 1) & (df["LiquidityOK"] == 1) & (df["MomentumScore"] > 0)].copy()
    entry_idx = eligible[eligible["FlowAligned"] == 1].head(config.trading_book_size).index
    hold_idx = eligible[eligible["FlowAligned"] == 1].iloc[config.trading_book_size :].index
    df.loc[hold_idx, "CandidateState"] = "HOLD"
    df.loc[entry_idx, "CandidateState"] = "ENTRY"
    df["MADTargetWeight"] = 0.0
    if len(entry_idx) > 0:
        entry_weights = _normalize_target_weight(df.loc[entry_idx], cap=config.trading_book_weight_cap)
        df.loc[entry_idx, "MADTargetWeight"] = entry_weights
    return df


def _grade_tenbagger_candidate(row: pd.Series) -> tuple[str, float]:
    if int(row["TrendOK"]) == 0 or float(row["R12M"]) <= 0 or float(row["R6M"]) <= 0:
        return "Exit Watch", 0.0
    if float(row["FlowAligned"]) == 1 and float(row["RelVolume20D60D"]) >= 1.10 and float(row["DistanceTo52WHigh"]) >= -0.08:
        return "Add-on", 0.06
    if float(row["FlowAligned"]) == 1:
        return "Starter", 0.04
    return "Watch", 0.02


def _build_tenbagger_watchlist(
    metrics: pd.DataFrame,
    flow_snapshot: pd.DataFrame,
    config: PipelineConfig,
) -> pd.DataFrame:
    allowed_countries, allowed_sectors = _allowed_labels(flow_snapshot, config)
    df = metrics[metrics["AssetType"] == "STOCK"].copy()
    df["CountryLabel"] = np.where(df["Market"].eq("US"), "US", "Korea")
    df["CountryAligned"] = df["CountryLabel"].isin(allowed_countries).astype(int)
    df["SectorAligned"] = [
        int(row.Sector in allowed_sectors.get(str(row.Market), set())) if str(row.Sector) != "Unknown" else 0
        for row in df.itertuples(index=False)
    ]
    min_values = np.where(df["Market"].eq("US"), config.us_min_median_value, config.kr_min_median_value)
    df["LiquidityOK"] = ((df["MedianDailyValue60D"] >= min_values) & (df["CurrentPrice"] >= config.min_price)).astype(int)
    df["FlowAligned"] = ((df["CountryAligned"] == 1) & ((df["SectorAligned"] == 1) | (df["Market"] == "KR"))).astype(int)
    df["StructureOK"] = ((df["LiquidityOK"] == 1) & (df["R6M"] > 0) & (df["R12M"] > 0)).astype(int)
    df = df[df["StructureOK"] == 1].copy()
    grades = df.apply(_grade_tenbagger_candidate, axis=1)
    df["WatchGrade"] = [grade for grade, _ in grades]
    df["InitialPositionCap"] = [cap for _, cap in grades]
    df["Theme"] = np.where(df["Sector"].fillna("").eq("Unknown"), "General Leader", df["Sector"])
    df["TrendState"] = np.where(df["TrendOK"] == 1, "LONG_UPTREND", "TREND_WEAKENING")
    df["TenbaggerScore"] = (
        0.35 * df["R6M"].fillna(0.0)
        + 0.35 * df["R12M"].fillna(0.0)
        + 0.15 * df["FlowScore"].fillna(0.0)
        + 0.15 * (df["RelVolume20D60D"].fillna(1.0) - 1.0)
    )
    df = df.sort_values(["TenbaggerScore", "MomentumScore", "Symbol"], ascending=[False, False, True]).reset_index(drop=True)
    return df


def _build_portfolio_trading_book(candidates: pd.DataFrame, config: PipelineConfig) -> pd.DataFrame:
    pool = candidates[candidates["CandidateState"].eq("ENTRY")].copy()
    if pool.empty:
        return pool
    picked = []
    market_counts: dict[str, int] = {}
    for row in pool.sort_values(["MomentumScore", "FlowScore"], ascending=[False, False]).itertuples(index=False):
        market = str(row.Market)
        if market_counts.get(market, 0) >= config.trading_book_market_cap:
            continue
        picked.append(row.Symbol)
        market_counts[market] = market_counts.get(market, 0) + 1
        if len(picked) >= config.trading_book_size:
            break
    book = pool[pool["Symbol"].isin(picked)].copy()
    book["TargetWeight"] = _normalize_target_weight(book, cap=config.trading_book_weight_cap)
    book = book.sort_values(["TargetWeight", "MomentumScore"], ascending=[False, False]).reset_index(drop=True)
    book["Book"] = "TRADING_BOOK"
    return book


def _build_portfolio_tenbagger_book(watchlist: pd.DataFrame, config: PipelineConfig) -> pd.DataFrame:
    pool = watchlist[watchlist["WatchGrade"].isin(["Starter", "Add-on"])].head(config.tenbagger_book_size).copy()
    if pool.empty:
        return pool
    pool["TargetWeight"] = _normalize_target_weight(pool, cap=config.tenbagger_weight_cap)
    pool["Book"] = "TENBAGGER_BOOK"
    pool = pool.sort_values(["TargetWeight", "TenbaggerScore"], ascending=[False, False]).reset_index(drop=True)
    return pool


def _write_summary(
    target_dir: Path,
    flow_snapshot: pd.DataFrame,
    momentum_candidates: pd.DataFrame,
    tenbagger_watchlist: pd.DataFrame,
    trading_book: pd.DataFrame,
    tenbagger_book: pd.DataFrame,
    kr_context: KRDataContext,
    readiness: pd.DataFrame,
) -> None:
    kr_stock_readiness = readiness[readiness["Scope"].eq("KR_STOCK")]
    stock_flow_missing = int(kr_stock_readiness["FlowMissingCount"].iloc[0]) if not kr_stock_readiness.empty else 0
    stock_price_missing = int(kr_stock_readiness["PriceMissingCount"].iloc[0]) if not kr_stock_readiness.empty else 0
    summary = {
        "AsOfDate": str(flow_snapshot["AsOfDate"].iloc[0]) if not flow_snapshot.empty else "",
        "ObserverRegime": str(flow_snapshot["Regime"].iloc[0]) if not flow_snapshot.empty else "",
        "AggressiveAllowed": int(flow_snapshot["AggressiveAllowed"].max()) if not flow_snapshot.empty else 0,
        "MomentumEntryCount": int(momentum_candidates["CandidateState"].eq("ENTRY").sum()),
        "TenbaggerWatchCount": int(len(tenbagger_watchlist)),
        "TradingBookCount": int(len(trading_book)),
        "TenbaggerBookCount": int(len(tenbagger_book)),
        "TopTradingBookSymbols": ",".join(trading_book["Symbol"].head(5).astype(str).tolist()),
        "TopTenbaggerSymbols": ",".join(tenbagger_book["Symbol"].head(5).astype(str).tolist()),
        "KRSourceLabel": kr_context.source_label,
        "KRUniversePath": str(kr_context.universe_path),
        "KRPriceRoot": str(kr_context.price_root),
        "KRFlowRoot": str(kr_context.flow_root) if kr_context.flow_root is not None else "",
        "KRStockPriceMissingCount": stock_price_missing,
        "KRStockFlowMissingCount": stock_flow_missing,
    }
    pd.DataFrame([summary]).to_csv(target_dir / "split_models_summary.csv", index=False, encoding="utf-8-sig")
    (target_dir / "split_models_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    readiness.to_csv(target_dir / "split_models_data_readiness.csv", index=False, encoding="utf-8-sig")
    (target_dir / "split_models_data_readiness.json").write_text(
        readiness.to_json(orient="records", indent=2, force_ascii=False),
        encoding="utf-8",
    )


def run_pipeline(output_dir: Path | None = None, config: PipelineConfig | None = None) -> dict[str, pd.DataFrame]:
    config = config or PipelineConfig()
    target_dir = output_dir or OUTPUT_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    kr_context = _discover_kr_data_context()
    readiness = _build_data_readiness(kr_context)

    us_stock_metrics = _load_us_stock_metrics()
    us_etf_metrics = _load_us_etf_metrics()
    kr_metrics = _load_kr_metrics(kr_context)
    all_metrics = pd.concat([us_stock_metrics, us_etf_metrics, kr_metrics], ignore_index=True)

    flow_snapshot = _build_flow_regime_snapshot(us_stock_metrics, us_etf_metrics, kr_metrics, config)
    momentum_candidates = _build_momentum_trade_candidates(all_metrics, flow_snapshot, config)
    tenbagger_watchlist = _build_tenbagger_watchlist(all_metrics, flow_snapshot, config)
    trading_book = _build_portfolio_trading_book(momentum_candidates, config)
    tenbagger_book = _build_portfolio_tenbagger_book(tenbagger_watchlist, config)

    flow_snapshot.to_csv(target_dir / "flow_regime_snapshot.csv", index=False, encoding="utf-8-sig")
    momentum_candidates.to_csv(target_dir / "momentum_trade_candidates.csv", index=False, encoding="utf-8-sig")
    tenbagger_watchlist.to_csv(target_dir / "tenbagger_watchlist.csv", index=False, encoding="utf-8-sig")
    trading_book.to_csv(target_dir / "portfolio_trading_book.csv", index=False, encoding="utf-8-sig")
    tenbagger_book.to_csv(target_dir / "portfolio_tenbagger_book.csv", index=False, encoding="utf-8-sig")
    _write_summary(
        target_dir,
        flow_snapshot,
        momentum_candidates,
        tenbagger_watchlist,
        trading_book,
        tenbagger_book,
        kr_context,
        readiness,
    )

    return {
        "flow_regime_snapshot": flow_snapshot,
        "momentum_trade_candidates": momentum_candidates,
        "tenbagger_watchlist": tenbagger_watchlist,
        "portfolio_trading_book": trading_book,
        "portfolio_tenbagger_book": tenbagger_book,
        "data_readiness": readiness,
    }
