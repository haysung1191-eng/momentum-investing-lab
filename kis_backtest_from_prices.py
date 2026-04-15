import argparse
import math
from dataclasses import dataclass
from dataclasses import field
from typing import Any, Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd

import config
from kis_flow_data import build_flow_matrices
from kis_flow_signal import compute_flow_score, compute_flow_score_v3, rank_flow_at
from kis_quality_data import build_quality_matrices, default_quality_base, rank_quality_at
from live_core.kis_io import build_close_matrix, build_market_matrices, list_price_files, read_price_file, write_csv_any
from live_core.kis_metrics import blend_component_metrics, summarize_backtest_metrics
from live_core.kis_strategy_config import build_default_strategies, strategy_runtime_kwargs
try:
    from tqdm.auto import tqdm
except Exception:  # pragma: no cover
    def tqdm(x, **kwargs):  # type: ignore
        return x


OVERHEAT_NORMAL = "정상"
OVERHEAT_CAUTION = "주의"
OVERHEAT_OVERHEATED = "과열"

HYBRID_STRATEGY_COMPONENTS: Dict[str, Dict[str, float]] = {
    "Weekly Hybrid RS50 RB50": {
        "Weekly Score50 RegimeState": 0.50,
        "Weekly ETF RiskBudget": 0.50,
    },
    "Weekly Hybrid Flow50 RS50": {
        "Weekly ForeignFlow v2": 0.50,
        "Weekly Score50 RegimeState": 0.50,
    },
    "Weekly Hybrid FV350 RS50": {
        "Weekly ForeignFlow v3": 0.50,
        "Weekly Score50 RegimeState": 0.50,
    },
    "Weekly Hybrid QP50 RS50": {
        "Weekly QualityProfitability MVP": 0.50,
        "Weekly Score50 RegimeState": 0.50,
    },
}

RESEARCH_ONLY_STRATEGY_NAMES = {
    "Weekly ForeignFlow v2",
    "Weekly ForeignFlow v3",
    "Weekly Hybrid Flow50 RS50",
    "Weekly Hybrid FV350 RS50",
    "Weekly QualityProfitability MVP",
    "Weekly Hybrid QP50 RS50",
}

OPERATIONAL_CANDIDATE_STRATEGY_NAMES = {
    "Weekly Score50 RegimeState",
    "Weekly ETF RiskBudget",
    "Weekly Hybrid RS50 RB50",
}


@dataclass
class StrategyConfig:
    name: str
    rebalance: str  # D, W-FRI
    top_n_stock: int
    top_n_etf: int
    fee_rate: float
    use_buffer: bool = False
    entry_rank: int = 20
    exit_rank: int = 25
    use_regime_filter: bool = False
    stop_loss_pct: float = 0.0
    trend_exit_ma: int = 0
    regime_ma_window: int = 200
    regime_slope_window: int = 20
    regime_breadth_threshold: float = 0.55
    vol_lookback: int = 20
    target_vol_annual: float = 0.20
    max_weight: float = 0.20
    min_gross_exposure: float = 0.50
    selection_mode: str = "topn"  # topn, score
    score_top_k: int = 50
    score_power: float = 1.5
    regime_off_exposure: float = 0.40
    mad_t1: float = 2.0
    mad_t2: float = 5.0
    mad_t3: float = 10.0
    mad_w1: float = 1.2
    mad_w2: float = 1.0
    mad_w3: float = 0.7
    mad_w4: float = 0.4
    allow_intraperiod_reentry: bool = True
    reentry_cooldown_days: int = 0
    use_regime_state_model: bool = False
    enable_oscillation_long: bool = False
    osc_lookback: int = 20
    osc_z_entry: float = -1.5
    osc_z_exit: float = -0.25
    osc_z_stop: float = -2.5
    osc_band_sigma: float = 1.5
    osc_band_break_sigma: float = 2.0
    osc_reentry_cooldown_days: int = 5
    range_slope_threshold: float = 0.015
    range_dist_threshold: float = 0.03
    range_breakout_persistence_threshold: float = 0.35
    range_breadth_tolerance: float = 0.15
    use_rotation_overlay: bool = False
    rotation_top_k: int = 5
    rotation_tilt_strength: float = 0.20
    rotation_min_sleeve_weight: float = 0.25
    fixed_sleeve_weights: Dict[str, float] = field(default_factory=dict)
    use_etf_risk_budget: bool = False
    risk_budget_lookback: int = 120
    risk_budget_shrinkage: float = 0.35
    risk_budget_iv_blend: float = 0.50
    use_foreign_flow_model: bool = False
    flow_model_version: int = 2
    flow_hold_buffer: int = 10
    flow_trend_ma: int = 60
    flow_foreign_ratio_cap: float = 40.0
    flow_foreign_ratio_penalty: float = 0.50
    use_quality_profitability_model: bool = False
    quality_hold_buffer: int = 10
    quality_trend_ma: int = 60
    use_point_in_time_universe: bool = True
    stock_universe_min_bars: int = 750
    stock_universe_min_price: float = 1000.0
    stock_universe_min_avg_value: float = 5_000_000_000.0
    stock_universe_min_median_value: float = 2_000_000_000.0
    stock_universe_max_zero_days: int = 1
    etf_universe_min_bars: int = 180
    etf_universe_min_avg_value: float = 500_000_000.0
    etf_universe_min_median_value: float = 100_000_000.0
    etf_universe_max_zero_days: int = 1


def is_hybrid_strategy_name(strategy_name: str) -> bool:
    return strategy_name in HYBRID_STRATEGY_COMPONENTS


def is_research_only_strategy_name(strategy_name: str) -> bool:
    return str(strategy_name) in RESEARCH_ONLY_STRATEGY_NAMES


def is_operational_candidate_strategy_name(strategy_name: str) -> bool:
    return str(strategy_name) in OPERATIONAL_CANDIDATE_STRATEGY_NAMES


def blend_strategy_results(
    strategy_name: str,
    component_results: Dict[str, Tuple[pd.DataFrame, Dict[str, float]]],
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    spec = HYBRID_STRATEGY_COMPONENTS.get(strategy_name)
    if spec is None:
        raise ValueError(f"Unsupported hybrid strategy: {strategy_name}")
    missing = [name for name in spec.keys() if name not in component_results]
    if missing:
        raise ValueError(f"Missing hybrid components for {strategy_name}: {missing}")

    daily_frames: List[pd.Series] = []
    for component_name in spec.keys():
        out, _ = component_results[component_name]
        if out is None or out.empty or "daily_return" not in out.columns:
            raise ValueError(f"Hybrid component {component_name} has no daily_return series.")
        daily_frames.append(out["daily_return"].rename(component_name))
    merged = pd.concat(daily_frames, axis=1, join="inner").fillna(0.0)
    if merged.empty:
        raise ValueError(f"Hybrid component overlap is empty for {strategy_name}.")

    out = pd.DataFrame(index=merged.index)
    out["daily_return"] = 0.0
    for component_name, weight in spec.items():
        out["daily_return"] = out["daily_return"] + float(weight) * merged[component_name]
    out["nav"] = (1.0 + out["daily_return"]).cumprod()
    metrics = blend_component_metrics(spec, component_results, out)
    return out, metrics


def default_flow_base() -> str:
    return f"gs://{config.GCS_BUCKET_NAME}/flows_naver_8y" if config.GCS_BUCKET_NAME else "data/flows_naver_8y"


def compute_point_in_time_universe(close: pd.DataFrame, traded_value: pd.DataFrame, market: str, stg: StrategyConfig) -> pd.DataFrame:
    if close.empty:
        return pd.DataFrame(index=close.index, columns=close.columns, dtype=bool)
    bars = close.notna().cumsum()
    avg_value_60 = traded_value.rolling(60, min_periods=60).mean()
    median_value_60 = traded_value.rolling(60, min_periods=60).median()
    zero_value_days_60 = traded_value.fillna(0.0).le(0.0).rolling(60, min_periods=60).sum()

    if market == "stock":
        return (
            (bars >= stg.stock_universe_min_bars)
            & (close >= stg.stock_universe_min_price)
            & (avg_value_60 >= stg.stock_universe_min_avg_value)
            & (median_value_60 >= stg.stock_universe_min_median_value)
            & (zero_value_days_60 <= stg.stock_universe_max_zero_days)
        ).fillna(False)
    return (
        (bars >= stg.etf_universe_min_bars)
        & (avg_value_60 >= stg.etf_universe_min_avg_value)
        & (median_value_60 >= stg.etf_universe_min_median_value)
        & (zero_value_days_60 <= stg.etf_universe_max_zero_days)
    ).fillna(False)


def add_scores(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    pos_count = (out[["r1", "r3", "r6", "r12"]] > 0).sum(axis=1)
    s1 = pos_count * 10.0
    s2 = ((out["avg_mom"].clip(-20, 80) + 20) / 100.0) * 25.0
    s3 = (20.0 - (out["mrat"] - 1.35).abs() * 25.0).clip(0, 20)
    s4 = (15.0 - (out["mad_gap"] - 20).abs() * 0.25).clip(0, 15)
    out["buy_score"] = s1 + s2 + s3 + s4
    out["overheat"] = OVERHEAT_NORMAL
    out.loc[(out["mad_gap"] >= 60) | (out["mrat"] >= 1.9), "overheat"] = OVERHEAT_CAUTION
    out.loc[(out["mad_gap"] >= 100) | (out["mrat"] >= 2.3) | (out["r1"] >= 45), "overheat"] = OVERHEAT_OVERHEATED
    return out


def features(close: pd.DataFrame, stg: StrategyConfig | None = None) -> Dict[str, pd.DataFrame]:
    osc_lookback = max(5, int(stg.osc_lookback)) if stg is not None else 20
    osc_band_sigma = float(stg.osc_band_sigma) if stg is not None else 1.5
    osc_band_break_sigma = float(stg.osc_band_break_sigma) if stg is not None else 2.0
    r1 = (close / close.shift(20) - 1) * 100
    r3 = (close / close.shift(60) - 1) * 100
    r6 = (close / close.shift(120) - 1) * 100
    r12 = (close / close.shift(240) - 1) * 100
    avg_mom = (r1 + r3 + r6 + r12) / 4
    ma21 = close.rolling(21, min_periods=21).mean()
    ma60 = close.rolling(60, min_periods=60).mean()
    ma200 = close.rolling(200, min_periods=200).mean()
    mrat = ma21 / ma200
    mad_gap = (ma21 - ma200) / ma200 * 100
    osc_mean = close.rolling(osc_lookback, min_periods=osc_lookback).mean()
    osc_std = close.rolling(osc_lookback, min_periods=osc_lookback).std(ddof=0).replace(0.0, np.nan)
    osc_z = (close - osc_mean) / osc_std
    osc_recovery = (close > close.shift(1)).astype(float)
    osc_lower_band = osc_mean - osc_band_sigma * osc_std
    osc_break = close < (osc_mean - osc_band_break_sigma * osc_std)
    osc_break_persist = osc_break.rolling(2, min_periods=1).sum()
    return {
        "r1": r1,
        "r3": r3,
        "r6": r6,
        "r12": r12,
        "avg_mom": avg_mom,
        "mrat": mrat,
        "mad_gap": mad_gap,
        "ma60": ma60,
        "osc_mean": osc_mean,
        "osc_std": osc_std,
        "osc_z": osc_z,
        "osc_recovery": osc_recovery,
        "osc_lower_band": osc_lower_band,
        "osc_break": osc_break.astype(float),
        "osc_break_persist": osc_break_persist,
    }


def feature_frame_at(feat: Dict[str, pd.DataFrame], dt: pd.Timestamp) -> pd.DataFrame:
    df = pd.DataFrame({k: v.loc[dt] for k, v in feat.items()}).dropna()
    if df.empty:
        return df
    df = df[np.isfinite(df).all(axis=1)]
    if df.empty:
        return df
    return add_scores(df)


def _merge_rank_frames(primary: pd.DataFrame, preserved: list[str], additions: pd.DataFrame, limit: int) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    seen: set[str] = set()
    for subset in [
        primary.loc[[t for t in preserved if t in primary.index]] if preserved else primary.iloc[0:0],
        additions,
        primary,
    ]:
        if subset.empty:
            continue
        subset = subset.loc[[t for t in subset.index if t not in seen]]
        if subset.empty:
            continue
        frames.append(subset)
        seen.update(subset.index)
        if len(seen) >= max(0, int(limit)):
            break
    if not frames:
        return primary.iloc[0:0]
    return pd.concat(frames, axis=0).head(max(0, int(limit)))


def _rotation_signal_from_ranks(rank_s: pd.DataFrame, rank_e: pd.DataFrame, stg: StrategyConfig) -> tuple[float, float, float]:
    if rank_s.empty or rank_e.empty:
        return 0.0, 0.5, 0.5
    top_k = max(1, int(stg.rotation_top_k))

    def _strength(df: pd.DataFrame) -> float:
        top = df.head(top_k)
        if top.empty:
            return 0.0
        score = float(top["buy_score"].astype(float).mean()) if "buy_score" in top.columns else 0.0
        mom = float(top["avg_mom"].astype(float).mean()) if "avg_mom" in top.columns else 0.0
        return score + 0.25 * mom

    stock_strength = _strength(rank_s)
    etf_strength = _strength(rank_e)
    denom = max(abs(stock_strength) + abs(etf_strength), 1e-9)
    raw_signal = float(np.clip((etf_strength - stock_strength) / denom, -1.0, 1.0))
    tilt = float(np.clip(stg.rotation_tilt_strength, 0.0, 0.45))
    min_sleeve = float(np.clip(stg.rotation_min_sleeve_weight, 0.0, 0.5))
    etf_target = float(np.clip(0.5 + tilt * raw_signal, min_sleeve, 1.0 - min_sleeve))
    stock_target = 1.0 - etf_target
    return raw_signal, stock_target, etf_target


def compute_regime_state(close_s: pd.DataFrame, stg: StrategyConfig) -> pd.DataFrame:
    market_proxy = close_s.mean(axis=1)
    market_ma = market_proxy.rolling(stg.regime_ma_window, min_periods=stg.regime_ma_window).mean()
    market_slope = market_ma - market_ma.shift(stg.regime_slope_window)
    slope_norm = (market_slope / market_ma.replace(0.0, np.nan)).replace([np.inf, -np.inf], np.nan)
    stock_ma = close_s.rolling(stg.regime_ma_window, min_periods=stg.regime_ma_window).mean()
    breadth = (close_s > stock_ma).mean(axis=1)
    dist_from_ma = ((market_proxy - market_ma) / market_ma.replace(0.0, np.nan)).replace([np.inf, -np.inf], np.nan)
    proxy_std = market_proxy.rolling(stg.osc_lookback, min_periods=stg.osc_lookback).std(ddof=0).replace(0.0, np.nan)
    proxy_z = ((market_proxy - market_ma) / proxy_std).replace([np.inf, -np.inf], np.nan)
    breakout_persist = (proxy_z.abs() >= 1.0).rolling(10, min_periods=5).mean()

    uptrend = (
        (market_proxy > market_ma)
        & (slope_norm > stg.range_slope_threshold)
        & (breadth >= stg.regime_breadth_threshold)
    )
    downtrend = (
        (market_proxy < market_ma)
        & (slope_norm < -stg.range_slope_threshold)
        & (breadth <= (1.0 - stg.regime_breadth_threshold))
    )
    breadth_mid_low = 0.5 - stg.range_breadth_tolerance
    breadth_mid_high = 0.5 + stg.range_breadth_tolerance
    range_regime = (
        (~uptrend)
        & (~downtrend)
        & (slope_norm.abs() <= stg.range_slope_threshold)
        & (dist_from_ma.abs() <= stg.range_dist_threshold)
        & (breakout_persist.fillna(0.0) <= stg.range_breakout_persistence_threshold)
        & breadth.between(breadth_mid_low, breadth_mid_high, inclusive="both")
    )

    labels = pd.Series("TRANSITION", index=close_s.index, dtype=object)
    labels.loc[uptrend.fillna(False)] = "UPTREND"
    labels.loc[downtrend.fillna(False)] = "DOWNTREND"
    labels.loc[range_regime.fillna(False)] = "RANGE"

    risk_on = labels.isin(["UPTREND", "RANGE"])
    if not stg.use_regime_state_model:
        legacy_risk_on = (market_proxy > market_ma) & (market_slope > 0) & (breadth >= stg.regime_breadth_threshold)
        legacy_risk_on = legacy_risk_on.fillna(True)
        if float(legacy_risk_on.mean()) < 0.10:
            legacy_risk_on = (market_proxy > market_ma).fillna(True)
        labels = pd.Series(np.where(legacy_risk_on, "UPTREND", "DOWNTREND"), index=close_s.index, dtype=object)
        risk_on = legacy_risk_on

    return pd.DataFrame(
        {
            "MarketProxy": market_proxy,
            "MarketMA": market_ma,
            "MarketSlope": market_slope,
            "SlopeNorm": slope_norm,
            "Breadth": breadth,
            "DistFromMA": dist_from_ma,
            "BreakoutPersistence": breakout_persist,
            "RiskOn": risk_on.fillna(True),
            "RegimeState": labels,
        }
    )


def oscillation_candidates_at(
    feat: Dict[str, pd.DataFrame],
    dt: pd.Timestamp,
    stg: StrategyConfig,
    eligible_mask: pd.DataFrame | None = None,
) -> pd.DataFrame:
    df = feature_frame_at(feat, dt)
    if df.empty:
        return df
    if eligible_mask is not None and dt in eligible_mask.index:
        eligible = eligible_mask.loc[dt].fillna(False)
        df = df.loc[df.index.intersection(eligible[eligible].index)]
        if df.empty:
            return df
    cond = (
        (df["osc_z"] <= stg.osc_z_entry)
        & (df["r1"] < 0)
        & (df["osc_recovery"] > 0)
        & (df["osc_break"] <= 0)
        & (df["osc_break_persist"] < 2)
        & (df["mad_gap"] <= stg.mad_t2)
        & (df["overheat"] != OVERHEAT_OVERHEATED)
    )
    out = df.loc[cond].copy()
    if out.empty:
        return out
    out["osc_priority"] = (-out["osc_z"]).clip(lower=0.0) + ((-out["r1"]).clip(lower=0.0) / 100.0)
    return out.sort_values(["osc_priority", "buy_score", "avg_mom"], ascending=[False, False, False])


def rebalance_dates(dates: Sequence[pd.Timestamp], rule: str) -> List[pd.Timestamp]:
    idx = pd.DatetimeIndex(dates)
    if rule == "D":
        return list(idx)
    if rule == "W-FRI":
        d = list(idx[idx.weekday == 4])
        if d and d[-1] != idx[-1]:
            d.append(idx[-1])
        if not d:
            d = [idx[-1]]
        return d
    if rule == "W-2FRI":
        fri = list(idx[idx.weekday == 4])
        d = fri[::2]
        if d and d[-1] != idx[-1]:
            d.append(idx[-1])
        if not d:
            d = [idx[-1]]
        return d
    raise ValueError(rule)


def select_buffer(ranked: List[str], prev: List[str], top_n: int, use_buffer: bool, entry_rank: int, exit_rank: int) -> List[str]:
    if not ranked:
        return []
    if not use_buffer:
        return ranked[:top_n]
    rmap = {t: i + 1 for i, t in enumerate(ranked)}
    kept = [t for t in prev if t in rmap and rmap[t] <= exit_rank]
    out = list(kept)
    for t in ranked:
        if rmap[t] <= entry_rank and t not in out:
            out.append(t)
        if len(out) >= top_n:
            break
    return out[:top_n]


def rank_at(feat: Dict[str, pd.DataFrame], dt: pd.Timestamp, eligible_mask: pd.DataFrame | None = None) -> pd.DataFrame:
    df = feature_frame_at(feat, dt)
    if df.empty:
        return df
    if eligible_mask is not None and dt in eligible_mask.index:
        eligible = eligible_mask.loc[dt].fillna(False)
        df = df.loc[df.index.intersection(eligible[eligible].index)]
        if df.empty:
            return df
    df = df[df["overheat"] != OVERHEAT_OVERHEATED]
    return df.sort_values(["buy_score", "avg_mom"], ascending=[False, False])


def _inverse_vol_weights(ret_window: pd.DataFrame, tickers: List[str]) -> Dict[str, float]:
    if not tickers:
        return {}
    if ret_window.empty:
        w = 1.0 / len(tickers)
        return {t: w for t in tickers}

    vol = ret_window[tickers].std(ddof=0).replace(0, np.nan)
    inv = 1.0 / vol
    inv = inv.replace([np.inf, -np.inf], np.nan).dropna()
    if inv.empty:
        w = 1.0 / len(tickers)
        return {t: w for t in tickers}
    inv = inv / inv.sum()
    out = {t: float(inv.get(t, 0.0)) for t in tickers}
    s = sum(out.values())
    if s <= 0:
        w = 1.0 / len(tickers)
        return {t: w for t in tickers}
    return {k: v / s for k, v in out.items()}


def _cap_weights_to_target(weights: Dict[str, float], max_weight: float, target_gross: float) -> Dict[str, float]:
    if not weights:
        return {}
    if max_weight <= 0:
        s = sum(weights.values())
        if s <= 0:
            return {}
        return {k: (v / s) * target_gross for k, v in weights.items()}

    n = len(weights)
    feasible_gross = min(target_gross, n * max_weight)
    if feasible_gross <= 0:
        return {}

    raw_sum = sum(weights.values())
    if raw_sum <= 0:
        return {}
    working = {k: v / raw_sum * feasible_gross for k, v in weights.items()}
    fixed: Dict[str, float] = {}

    while True:
        over = [k for k, v in working.items() if v > max_weight + 1e-12]
        if not over:
            break
        for k in over:
            fixed[k] = max_weight
            working.pop(k, None)
        rem_target = feasible_gross - sum(fixed.values())
        if rem_target <= 1e-12 or not working:
            working = {}
            break
        rem_sum = sum(working.values())
        if rem_sum <= 0:
            working = {}
            break
        scale = rem_target / rem_sum
        working = {k: v * scale for k, v in working.items()}

    out = {}
    out.update(fixed)
    out.update(working)
    return dict(sorted(out.items()))


def _risk_budget_weights(ret_window: pd.DataFrame, tickers: List[str], stg: StrategyConfig) -> Dict[str, float]:
    if not tickers:
        return {}
    if ret_window.empty or len(ret_window) < 10:
        w = 1.0 / len(tickers)
        return {t: w for t in tickers}
    cols = [t for t in tickers if t in ret_window.columns]
    if not cols:
        return {}
    sample = ret_window[cols].dropna(how="all")
    if len(sample) < 10:
        w = 1.0 / len(cols)
        return {t: w for t in cols}
    vol = sample.std(ddof=0).replace(0.0, np.nan)
    inv = (1.0 / vol).replace([np.inf, -np.inf], np.nan).dropna()
    inv = inv / inv.sum() if not inv.empty else pd.Series(dtype=float)
    cov = sample.cov().fillna(0.0)
    if cov.empty:
        w = 1.0 / len(cols)
        return {t: w for t in cols}
    alpha = float(np.clip(stg.risk_budget_shrinkage, 0.0, 1.0))
    diag = np.diag(np.diag(cov.values))
    shrunk = ((1.0 - alpha) * cov.values) + (alpha * diag)
    ridge = 1e-6 * np.eye(len(cols))
    ones = np.ones(len(cols), dtype=float)
    try:
        raw = np.linalg.solve(shrunk + ridge, ones)
    except np.linalg.LinAlgError:
        if inv.empty:
            w = 1.0 / len(cols)
            return {t: w for t in cols}
        inv = inv / inv.sum()
        return {str(k): float(v) for k, v in inv.items()}
    raw = np.clip(raw, 0.0, None)
    if float(raw.sum()) <= 0.0:
        w = 1.0 / len(cols)
        return {t: w for t in cols}
    raw = raw / raw.sum()
    weights = pd.Series({str(t): float(w) for t, w in zip(cols, raw)})
    blend = float(np.clip(stg.risk_budget_iv_blend, 0.0, 1.0))
    if blend > 0.0 and not inv.empty:
        inv = inv.reindex(weights.index).fillna(0.0)
        if float(inv.sum()) > 0.0:
            inv = inv / inv.sum()
            weights = ((1.0 - blend) * weights) + (blend * inv)
            weights = weights.clip(lower=0.0)
            if float(weights.sum()) > 0.0:
                weights = weights / weights.sum()
    return {str(k): float(v) for k, v in weights.items() if float(v) > 0.0}


def _mad_multiplier(gap_pct: float, stg: StrategyConfig) -> float:
    if not np.isfinite(gap_pct):
        return stg.mad_w2
    if gap_pct < stg.mad_t1:
        return stg.mad_w1
    if gap_pct < stg.mad_t2:
        return stg.mad_w2
    if gap_pct < stg.mad_t3:
        return stg.mad_w3
    return stg.mad_w4


def _score_weights_from_rank(df_rank: pd.DataFrame, stg: StrategyConfig) -> Dict[str, float]:
    if df_rank is None or df_rank.empty:
        return {}
    picked = df_rank.head(max(1, int(stg.score_top_k))).copy()
    if picked.empty:
        return {}

    s = picked["buy_score"].clip(lower=0.0).pow(stg.score_power)
    mad_scale = picked["mad_gap"].apply(lambda x: _mad_multiplier(float(x), stg))
    raw = (s * mad_scale).replace([np.inf, -np.inf], np.nan).dropna()
    raw = raw[raw > 0]
    if raw.empty:
        return {}
    raw = raw / raw.sum()
    return {str(k): float(v) for k, v in raw.items()}


def run_one(
    close_s: pd.DataFrame,
    close_e: pd.DataFrame,
    stg: StrategyConfig,
    min_common_dates: int,
    traded_value_s: pd.DataFrame | None = None,
    traded_value_e: pd.DataFrame | None = None,
    flow_mats: Dict[str, pd.DataFrame] | None = None,
    quality_mats: Dict[str, pd.DataFrame] | None = None,
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    dates = sorted(set(close_s.index).intersection(set(close_e.index)))
    if len(dates) < min_common_dates:
        raise RuntimeError(f"Not enough common dates. Need at least {min_common_dates}.")
    dates = pd.DatetimeIndex(dates)
    cs, ce = close_s.loc[dates], close_e.loc[dates]
    rs, re = cs.pct_change(fill_method=None).fillna(0.0), ce.pct_change(fill_method=None).fillna(0.0)
    fs, fe = features(cs, stg), features(ce, stg)
    universe_s = compute_point_in_time_universe(cs, traded_value_s.loc[dates, cs.columns] if traded_value_s is not None else pd.DataFrame(index=cs.index, columns=cs.columns), "stock", stg) if stg.use_point_in_time_universe and traded_value_s is not None else None
    universe_e = compute_point_in_time_universe(ce, traded_value_e.loc[dates, ce.columns] if traded_value_e is not None else pd.DataFrame(index=ce.index, columns=ce.columns), "etf", stg) if stg.use_point_in_time_universe and traded_value_e is not None else None
    flow_score = None
    if stg.use_foreign_flow_model:
        if traded_value_s is None or flow_mats is None:
            raise RuntimeError(f"{stg.name} requires traded_value_s and flow_mats.")
        flow_fn = compute_flow_score_v3 if int(getattr(stg, "flow_model_version", 2)) >= 3 else compute_flow_score
        flow_score = flow_fn(
            cs,
            traded_value_s.loc[dates, cs.columns],
            flow_mats,
            foreign_ratio_cap=stg.flow_foreign_ratio_cap,
            foreign_ratio_penalty=stg.flow_foreign_ratio_penalty,
        ).reindex(index=dates, columns=cs.columns)
    if stg.use_quality_profitability_model and quality_mats is None:
        raise RuntimeError(f"{stg.name} requires quality_mats.")
    ma_trend_s = cs.rolling(stg.trend_exit_ma, min_periods=stg.trend_exit_ma).mean() if stg.trend_exit_ma > 0 else pd.DataFrame(index=cs.index, columns=cs.columns)
    ma_trend_e = ce.rolling(stg.trend_exit_ma, min_periods=stg.trend_exit_ma).mean() if stg.trend_exit_ma > 0 else pd.DataFrame(index=ce.index, columns=ce.columns)
    reb = set(rebalance_dates(dates, stg.rebalance))
    regime_df = compute_regime_state(cs, stg)
    risk_on = regime_df["RiskOn"]
    regime_state = regime_df["RegimeState"]

    hold_s: List[str] = []
    hold_e: List[str] = []
    w_now: Dict[str, float] = {}
    entry_px: Dict[str, float] = {}
    entry_reason: Dict[str, str] = {}
    turns: List[float] = []
    exposures: List[float] = []
    holdings_count: List[int] = []
    rebalance_dates_log: List[pd.Timestamp] = []
    trade_buy_count = 0
    trade_sell_count = 0
    cooldown_left: Dict[str, int] = {}
    osc_entry_count = 0
    osc_exit_count = 0
    osc_stop_count = 0
    rotation_signals: List[float] = []
    stock_sleeves: List[float] = []
    etf_sleeves: List[float] = []
    rows = []

    for i in range(1, len(dates)):
        prev_dt, dt = dates[i - 1], dates[i]
        # Cooldown is counted in trading days.
        if cooldown_left:
            for t in list(cooldown_left.keys()):
                cooldown_left[t] -= 1
                if cooldown_left[t] <= 0:
                    cooldown_left.pop(t, None)

        fee = 0.0
        scheduled_rebalance = prev_dt in reb
        rebalance_now = scheduled_rebalance

        # Optional intraperiod exits.
        if hold_s or hold_e:
            keep_s: List[str] = []
            for t in hold_s:
                px = cs.at[prev_dt, t] if t in cs.columns else np.nan
                if pd.isna(px):
                    continue
                stop_hit = stg.stop_loss_pct > 0 and t in entry_px and px <= entry_px[t] * (1.0 - stg.stop_loss_pct)
                trend_hit = False
                if stg.trend_exit_ma > 0:
                    ma = ma_trend_s.at[prev_dt, t] if t in ma_trend_s.columns else np.nan
                    if pd.notna(ma):
                        trend_hit = px < ma
                osc_take_profit = False
                osc_invalid = False
                if entry_reason.get(t) == "osc":
                    osc_z = fs["osc_z"].at[prev_dt, t] if t in fs["osc_z"].columns else np.nan
                    osc_mean = fs["osc_mean"].at[prev_dt, t] if t in fs["osc_mean"].columns else np.nan
                    osc_break_persist = fs["osc_break_persist"].at[prev_dt, t] if t in fs["osc_break_persist"].columns else np.nan
                    osc_take_profit = pd.notna(osc_z) and float(osc_z) >= stg.osc_z_exit
                    if pd.notna(osc_mean):
                        osc_take_profit = bool(osc_take_profit or px >= osc_mean)
                    osc_invalid = (
                        (pd.notna(osc_z) and float(osc_z) <= stg.osc_z_stop)
                        or (pd.notna(osc_break_persist) and float(osc_break_persist) >= 2.0)
                        or (stg.use_regime_state_model and str(regime_state.get(prev_dt, "TRANSITION")) != "RANGE")
                    )
                if stop_hit or trend_hit or osc_take_profit or osc_invalid:
                    if entry_reason.get(t) == "osc":
                        osc_exit_count += 1
                        if stop_hit or osc_invalid:
                            osc_stop_count += 1
                    if entry_reason.get(t) == "osc" and (stop_hit or osc_invalid):
                        cd_days = stg.osc_reentry_cooldown_days
                    else:
                        cd_days = stg.reentry_cooldown_days
                    if cd_days > 0:
                        cooldown_left[t] = int(cd_days)
                    entry_reason.pop(t, None)
                else:
                    keep_s.append(t)
            keep_e: List[str] = []
            for t in hold_e:
                px = ce.at[prev_dt, t] if t in ce.columns else np.nan
                if pd.isna(px):
                    continue
                stop_hit = stg.stop_loss_pct > 0 and t in entry_px and px <= entry_px[t] * (1.0 - stg.stop_loss_pct)
                trend_hit = False
                if stg.trend_exit_ma > 0:
                    ma = ma_trend_e.at[prev_dt, t] if t in ma_trend_e.columns else np.nan
                    if pd.notna(ma):
                        trend_hit = px < ma
                if stop_hit or trend_hit:
                    if stg.reentry_cooldown_days > 0:
                        cooldown_left[t] = int(stg.reentry_cooldown_days)
                    entry_reason.pop(t, None)
                else:
                    keep_e.append(t)
            if keep_s != hold_s or keep_e != hold_e:
                hold_s, hold_e = keep_s, keep_e
                rebalance_now = True

        if rebalance_now:
            regime_name = str(regime_state.get(prev_dt, "TRANSITION"))
            regime_on = bool(risk_on.get(prev_dt, False))
            regime_target_exposure = 1.0
            if stg.use_regime_filter and not regime_on:
                regime_target_exposure = float(np.clip(stg.regime_off_exposure, 0.0, 1.0))

            do_reentry = scheduled_rebalance or stg.allow_intraperiod_reentry
            rank_s = rank_at(fs, prev_dt, universe_s) if do_reentry else pd.DataFrame()
            rank_e = rank_at(fe, prev_dt, universe_e) if do_reentry else pd.DataFrame()
            rank_s_use = rank_s
            osc_rank_s = pd.DataFrame()
            if do_reentry and stg.enable_oscillation_long and regime_name == "RANGE":
                osc_rank_s = oscillation_candidates_at(fs, prev_dt, stg, universe_s)

            if regime_target_exposure <= 0:
                hold_s, hold_e = [], []
            elif do_reentry and stg.use_etf_risk_budget:
                hold_s = []
                if universe_e is not None and prev_dt in universe_e.index:
                    eligible_etfs = list(universe_e.columns[universe_e.loc[prev_dt].fillna(False)])
                else:
                    eligible_etfs = list(ce.columns)
                if traded_value_e is not None and eligible_etfs:
                    recent_liq = traded_value_e.loc[:prev_dt, eligible_etfs].tail(60).median().sort_values(ascending=False)
                    eligible_etfs = [t for t in recent_liq.index if pd.notna(recent_liq[t]) and recent_liq[t] > 0]
                if stg.top_n_etf > 0:
                    eligible_etfs = eligible_etfs[: int(stg.top_n_etf)]
                hold_e = [t for t in eligible_etfs if cooldown_left.get(t, 0) <= 0]
            elif do_reentry and stg.use_foreign_flow_model:
                hold_e = []
                rank_s_use = rank_flow_at(
                    fs,
                    flow_score if flow_score is not None else pd.DataFrame(),
                    cs,
                    prev_dt,
                    universe_s,
                    stg.flow_trend_ma,
                    hold_s,
                    max(1, int(stg.score_top_k)),
                    stg.flow_hold_buffer,
                )
                if stg.use_regime_filter and not regime_on:
                    hold_s = []
                else:
                    hold_s = list(rank_s_use.index)[: max(1, int(stg.score_top_k))]
            elif do_reentry and stg.use_quality_profitability_model:
                hold_e = []
                rank_s_use = rank_quality_at(
                    fs,
                    quality_mats if quality_mats is not None else {},
                    prev_dt,
                    universe_s,
                    cs,
                    stg.quality_trend_ma,
                    hold_s,
                    max(1, int(stg.score_top_k)),
                    stg.quality_hold_buffer,
                )
                if stg.use_regime_filter and not regime_on:
                    hold_s = []
                else:
                    hold_s = list(rank_s_use.index)[: max(1, int(stg.score_top_k))]
            elif do_reentry:
                if stg.enable_oscillation_long and regime_name == "RANGE" and not osc_rank_s.empty:
                    preserved_hold_s = [t for t in hold_s if t in rank_s.index]
                    new_osc = osc_rank_s.loc[[t for t in osc_rank_s.index if cooldown_left.get(t, 0) <= 0 and t not in hold_s]]
                    selected_rank_s = _merge_rank_frames(
                        rank_s,
                        preserved_hold_s,
                        new_osc,
                        max(1, int(stg.score_top_k if stg.selection_mode == "score" else stg.top_n_stock)),
                    )
                    cand_s = list(selected_rank_s.index)
                elif regime_name in {"DOWNTREND", "TRANSITION"} and stg.use_regime_state_model:
                    preserved_hold_s = [t for t in hold_s if t in rank_s.index]
                    selected_rank_s = rank_s.loc[preserved_hold_s] if preserved_hold_s else rank_s.iloc[0:0]
                    cand_s = list(selected_rank_s.index)
                else:
                    cand_s = [t for t in list(rank_s.index) if cooldown_left.get(t, 0) <= 0]
                    selected_rank_s = rank_s
                cand_e = [t for t in list(rank_e.index) if cooldown_left.get(t, 0) <= 0]
                if stg.selection_mode == "score":
                    hold_s = cand_s[: max(1, int(stg.score_top_k))]
                    hold_e = cand_e[: max(1, int(stg.score_top_k))]
                else:
                    hold_s = select_buffer(cand_s, hold_s, stg.top_n_stock, stg.use_buffer, stg.entry_rank, stg.exit_rank)
                    hold_e = select_buffer(cand_e, hold_e, stg.top_n_etf, stg.use_buffer, stg.entry_rank, stg.exit_rank)
                rank_s_use = selected_rank_s

            # Build target weights: topn->inverse-vol, score->score-weight * MAD scaling.
            w_tar: Dict[str, float] = {}
            ret_s = rs.loc[:prev_dt].tail(stg.vol_lookback)
            ret_e = re.loc[:prev_dt].tail(stg.vol_lookback)
            if stg.use_etf_risk_budget:
                w_s = {}
                w_e = _risk_budget_weights(re.loc[:prev_dt].tail(max(20, int(stg.risk_budget_lookback))), hold_e, stg)
            elif stg.use_foreign_flow_model:
                if hold_s:
                    equal_w = 1.0 / len(hold_s)
                    w_s = {ticker: equal_w for ticker in hold_s}
                else:
                    w_s = {}
                w_e = {}
            elif stg.selection_mode == "score":
                w_s = _score_weights_from_rank(rank_s_use.loc[rank_s_use.index.intersection(hold_s)], stg)
                w_e = _score_weights_from_rank(rank_e.loc[rank_e.index.intersection(hold_e)], stg)
            else:
                w_s = _inverse_vol_weights(ret_s, hold_s)
                w_e = _inverse_vol_weights(ret_e, hold_e)
            rotation_signal = 0.0
            stock_sleeve = 0.5
            etf_sleeve = 0.5
            if stg.fixed_sleeve_weights:
                stock_sleeve = float(np.clip(stg.fixed_sleeve_weights.get("stock", 0.0), 0.0, 1.0))
                etf_sleeve = float(np.clip(stg.fixed_sleeve_weights.get("etf", 0.0), 0.0, 1.0))
                total_sleeve = stock_sleeve + etf_sleeve
                if total_sleeve > 0:
                    stock_sleeve /= total_sleeve
                    etf_sleeve /= total_sleeve
                rotation_signal = float(etf_sleeve - stock_sleeve)
            elif stg.use_rotation_overlay and w_s and w_e:
                rotation_signal, stock_sleeve, etf_sleeve = _rotation_signal_from_ranks(rank_s_use, rank_e, stg)
            if w_s and w_e:
                w_tar.update({k: v * stock_sleeve for k, v in w_s.items()})
                w_tar.update({k: v * etf_sleeve for k, v in w_e.items()})
            elif w_s:
                w_tar.update(w_s)
                stock_sleeve, etf_sleeve = 1.0, 0.0
            elif w_e:
                w_tar.update(w_e)
                stock_sleeve, etf_sleeve = 0.0, 1.0
            rotation_signals.append(rotation_signal)
            stock_sleeves.append(stock_sleeve)
            etf_sleeves.append(etf_sleeve)

            target_gross = regime_target_exposure
            # Vol targeting at portfolio level; allow a minimum gross floor to avoid over-deleveraging.
            if w_tar and stg.target_vol_annual > 0:
                ret_mix = pd.concat([ret_s, ret_e], axis=1)
                cols = [c for c in w_tar.keys() if c in ret_mix.columns]
                if len(cols) > 1 and len(ret_mix) >= 5:
                    cov = ret_mix[cols].cov().fillna(0.0)
                    wv = np.array([w_tar[c] for c in cols], dtype=float)
                    port_var = float(wv @ cov.values @ wv)
                    port_vol = math.sqrt(max(port_var, 0.0)) * math.sqrt(252)
                    if np.isfinite(port_vol) and port_vol > 1e-9:
                        scale = min(1.0, stg.target_vol_annual / port_vol)
                        scaled_gross = regime_target_exposure * scale
                        floor = stg.min_gross_exposure if regime_on else min(stg.min_gross_exposure, regime_target_exposure)
                        target_gross = max(floor, scaled_gross)
            target_gross = min(target_gross, regime_target_exposure)

            # Name-level concentration cap while trying to keep target gross exposure.
            w_tar = _cap_weights_to_target(w_tar, stg.max_weight, target_gross)

            uni = set(w_now) | set(w_tar)
            turn = sum(abs(w_tar.get(k, 0.0) - w_now.get(k, 0.0)) for k in uni)
            turns.append(turn)
            fee = turn * stg.fee_rate
            rebalance_dates_log.append(prev_dt)

            removed = set(w_now) - set(w_tar)
            added = set(w_tar) - set(w_now)
            trade_sell_count += len(removed)
            trade_buy_count += len(added)
            for t in removed:
                entry_px.pop(t, None)
                entry_reason.pop(t, None)
            for t in added:
                if t.startswith("S_") and t in cs.columns:
                    px = cs.at[prev_dt, t]
                elif t in ce.columns:
                    px = ce.at[prev_dt, t]
                else:
                    px = np.nan
                if pd.notna(px):
                    entry_px[t] = float(px)
                is_osc = bool(stg.enable_oscillation_long and regime_name == "RANGE" and t in osc_rank_s.index)
                entry_reason[t] = "osc" if is_osc else "momo"
                if is_osc:
                    osc_entry_count += 1

            w_now = w_tar
            exposures.append(sum(w_now.values()))

        day = 0.0
        for t, w in w_now.items():
            if t.startswith("S_"):
                r = rs.at[dt, t] if t in rs.columns else 0.0
            else:
                r = re.at[dt, t] if t in re.columns else 0.0
            if pd.isna(r):
                r = 0.0
            day += w * float(r)
        day -= fee

        rows.append({"date": dt, "daily_return": day})
        holdings_count.append(len(w_now))

    out = pd.DataFrame(rows).set_index("date")
    out["nav"] = (1.0 + out["daily_return"]).cumprod()
    metrics = summarize_backtest_metrics(
        out,
        turns=turns,
        exposures=exposures,
        holdings_count=holdings_count,
        rebalance_dates_log=rebalance_dates_log,
        trade_buy_count=trade_buy_count,
        trade_sell_count=trade_sell_count,
        regime_state=regime_state,
        osc_entry_count=osc_entry_count,
        osc_exit_count=osc_exit_count,
        osc_stop_count=osc_stop_count,
        rotation_signals=rotation_signals,
        stock_sleeves=stock_sleeves,
        etf_sleeves=etf_sleeves,
    )
    return out, metrics


def main() -> None:
    p = argparse.ArgumentParser(description="Run momentum backtests from KIS daily OHLCV close-price csv.gz data.")
    p.add_argument("--base", type=str, default=(f"gs://{config.GCS_BUCKET_NAME}/prices" if config.GCS_BUCKET_NAME else "data/prices"))
    p.add_argument("--top-n", type=int, default=20)
    p.add_argument("--fee-bps", type=float, default=8.0)
    p.add_argument("--max-files", type=int, default=0, help="0 means all")
    p.add_argument("--save-prefix", type=str, default="kis_backtest")
    p.add_argument("--min-common-dates", type=int, default=180)
    p.add_argument("--regime-filter", type=int, default=1, help="1 enables market MA200 risk-on filter")
    p.add_argument("--stop-loss-pct", type=float, default=0.12, help="Per-position stop loss, e.g. 0.10")
    p.add_argument("--trend-exit-ma", type=int, default=60, help="Exit when price falls below MA window; 0 disables")
    p.add_argument("--regime-ma-window", type=int, default=200)
    p.add_argument("--regime-slope-window", type=int, default=20)
    p.add_argument("--regime-breadth-threshold", type=float, default=0.55, help="Risk-on breadth threshold in [0,1]")
    p.add_argument("--vol-lookback", type=int, default=20)
    p.add_argument("--target-vol-annual", type=float, default=0.20, help="Annualized target volatility; <=0 disables")
    p.add_argument("--max-weight", type=float, default=0.20, help="Per-name cap; <=0 disables")
    p.add_argument("--min-gross-exposure", type=float, default=0.50, help="Minimum invested exposure in risk-on, [0,1]")
    p.add_argument("--score-top-k", type=int, default=50, help="Top-K universe size for score-weight mode")
    p.add_argument("--score-power", type=float, default=1.5, help="Power transform for score-weight mode")
    p.add_argument("--regime-off-exposure", type=float, default=0.40, help="Target gross exposure in risk-off regime")
    p.add_argument("--allow-intraperiod-reentry", type=int, default=1, help="1 allows same-day re-entry after stop/trend exits")
    p.add_argument("--reentry-cooldown-days", type=int, default=0, help="Trading-day cooldown after stop/trend exits")
    p.add_argument("--range-slope-threshold", type=float, default=0.015)
    p.add_argument("--range-dist-threshold", type=float, default=0.03)
    p.add_argument("--range-breakout-persistence-threshold", type=float, default=0.35)
    p.add_argument("--range-breadth-tolerance", type=float, default=0.15)
    p.add_argument("--osc-lookback", type=int, default=20)
    p.add_argument("--osc-z-entry", type=float, default=-1.5)
    p.add_argument("--osc-z-exit", type=float, default=-0.25)
    p.add_argument("--osc-z-stop", type=float, default=-2.5)
    p.add_argument("--osc-band-sigma", type=float, default=1.5)
    p.add_argument("--osc-band-break-sigma", type=float, default=2.0)
    p.add_argument("--osc-reentry-cooldown-days", type=int, default=5)
    p.add_argument("--rotation-top-k", type=int, default=5)
    p.add_argument("--rotation-tilt-strength", type=float, default=0.20)
    p.add_argument("--rotation-min-sleeve-weight", type=float, default=0.25)
    p.add_argument("--risk-budget-lookback", type=int, default=120)
    p.add_argument("--risk-budget-shrinkage", type=float, default=0.35)
    p.add_argument("--risk-budget-iv-blend", type=float, default=0.50)
    p.add_argument("--flow-base", type=str, default=default_flow_base())
    p.add_argument("--quality-base", type=str, default=default_quality_base())
    p.add_argument("--quality-hold-buffer", type=int, default=10)
    p.add_argument("--quality-trend-ma", type=int, default=60)
    p.add_argument("--use-point-in-time-universe", type=int, default=1)
    p.add_argument("--stock-universe-min-bars", type=int, default=750)
    p.add_argument("--stock-universe-min-price", type=float, default=1000.0)
    p.add_argument("--stock-universe-min-avg-value", type=float, default=5_000_000_000.0)
    p.add_argument("--stock-universe-min-median-value", type=float, default=2_000_000_000.0)
    p.add_argument("--stock-universe-max-zero-days", type=int, default=1)
    p.add_argument("--etf-universe-min-bars", type=int, default=180)
    p.add_argument("--etf-universe-min-avg-value", type=float, default=500_000_000.0)
    p.add_argument("--etf-universe-min-median-value", type=float, default=100_000_000.0)
    p.add_argument("--etf-universe-max-zero-days", type=int, default=1)
    args = p.parse_args()

    print("loading stock close matrix...")
    close_s, value_s = build_market_matrices(args.base, "stock", args.max_files)
    print("loading etf close matrix...")
    close_e, value_e = build_market_matrices(args.base, "etf", args.max_files)
    print(f"stock_tickers={close_s.shape[1]}, etf_tickers={close_e.shape[1]}")

    fee = args.fee_bps / 10000.0
    use_regime = bool(args.regime_filter)
    strategies = build_default_strategies(args, StrategyConfig, fee_rate=fee, use_regime_filter=use_regime)

    summary = []
    nav = None
    strategy_outputs: Dict[str, Tuple[pd.DataFrame, Dict[str, float]]] = {}
    flow_mats = build_flow_matrices(args.flow_base, market="stock", max_files=args.max_files)
    quality_mats = build_quality_matrices(args.quality_base, close_s.index, list(close_s.columns))
    for s in strategies:
        print(f"running {s.name}...")
        out, m = run_one(
            close_s,
            close_e,
            s,
            min_common_dates=args.min_common_dates,
            traded_value_s=value_s,
            traded_value_e=value_e,
            flow_mats=flow_mats,
            quality_mats=quality_mats,
        )
        row = {"Strategy": s.name}
        row.update(m)
        summary.append(row)
        strategy_outputs[s.name] = (out, m)
        if nav is None:
            nav = pd.DataFrame(index=out.index)
        nav[s.name] = out["nav"]

    for hybrid_name in HYBRID_STRATEGY_COMPONENTS.keys():
        if not all(component_name in strategy_outputs for component_name in HYBRID_STRATEGY_COMPONENTS[hybrid_name].keys()):
            continue
        print(f"running {hybrid_name}...")
        out, m = blend_strategy_results(hybrid_name, strategy_outputs)
        row = {"Strategy": hybrid_name}
        row.update(m)
        summary.append(row)
        nav[hybrid_name] = out["nav"]

    s_df = pd.DataFrame(summary)
    print("\n=== KIS Price Backtest ===")
    print(s_df.to_string(index=False))

    sum_path = f"{args.save_prefix}_summary.csv"
    nav_path = f"{args.save_prefix}_nav.csv"
    write_csv_any(s_df, sum_path, index=False)
    write_csv_any(nav, nav_path, index=True)
    print(f"saved {sum_path}")
    print(f"saved {nav_path}")


if __name__ == "__main__":
    main()
