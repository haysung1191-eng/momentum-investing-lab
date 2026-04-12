import json
import re
from io import BytesIO
from types import SimpleNamespace
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

import config
from kis_backtest_from_prices import (
    HYBRID_STRATEGY_COMPONENTS,
    StrategyConfig,
    _cap_weights_to_target,
    _inverse_vol_weights,
    _risk_budget_weights,
    _rotation_signal_from_ranks,
    _score_weights_from_rank,
    build_market_matrices,
    compute_point_in_time_universe,
    compute_regime_state,
    default_flow_base,
    feature_frame_at,
    features,
    is_hybrid_strategy_name,
    strategy_runtime_kwargs,
    _merge_rank_frames,
    oscillation_candidates_at,
    rank_at,
    rebalance_dates,
    select_buffer,
)
from kis_flow_data import build_flow_matrices
from kis_flow_signal import compute_flow_score, compute_flow_score_v3, rank_flow_at
from kis_quality_data import build_quality_matrices, default_quality_base, rank_quality_at


SCORE_NAME_RE = re.compile(r"^ScoreN(?P<n>\d+)_P(?P<power>\d+(?:\.\d+)?)_ROE(?P<roe>\d+(?:\.\d+)?)$")


def default_backtests_base() -> str:
    return f"gs://{config.GCS_BUCKET_NAME}/backtests" if config.GCS_BUCKET_NAME else "."


def read_csv_any(path: str) -> pd.DataFrame:
    try:
        if path.startswith("gs://"):
            from google.cloud import storage

            no_scheme = path.replace("gs://", "", 1)
            bucket_name, blob_name = no_scheme.split("/", 1) if "/" in no_scheme else (no_scheme, "")
            raw = storage.Client().bucket(bucket_name).blob(blob_name).download_as_bytes()
            return pd.read_csv(BytesIO(raw))
        return pd.read_csv(path)
    except Exception as e:
        print(f"[WARN] could not read {path}: {e}")
        return pd.DataFrame()


def read_json_any(path: str) -> dict[str, Any]:
    try:
        if path.startswith("gs://"):
            from google.cloud import storage

            no_scheme = path.replace("gs://", "", 1)
            bucket_name, blob_name = no_scheme.split("/", 1) if "/" in no_scheme else (no_scheme, "")
            text = storage.Client().bucket(bucket_name).blob(blob_name).download_as_text(encoding="utf-8")
            return json.loads(text)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] could not read {path}: {e}")
        return {}


def resolve_strategy_name(live_readiness_path: str, strategy_name: str | None = None) -> str:
    if strategy_name:
        return strategy_name
    ready = read_csv_any(live_readiness_path)
    if ready.empty or "Strategy" not in ready.columns:
        raise RuntimeError("live_readiness is unavailable or invalid; pass --strategy-name explicitly.")
    if "Recommendation" in ready.columns:
        rec = ready["Recommendation"].astype(str)
        for token in ("START_SMALL_LIVE_FIRST", "START_PAPER_FIRST"):
            preferred = ready[rec.eq(token)]
            if not preferred.empty:
                return str(preferred.iloc[0]["Strategy"])
    return str(ready.iloc[0]["Strategy"])


def parse_as_of_date(as_of_date: str | None) -> pd.Timestamp | None:
    if not as_of_date:
        return None
    return pd.Timestamp(as_of_date)


def _manifest_step_args(manifest_path: str | None, step_name: str = "baseline") -> dict[str, str]:
    if not manifest_path:
        return {}
    manifest = read_json_any(manifest_path)
    steps = manifest.get("steps", []) if isinstance(manifest, dict) else []
    for step in steps:
        if not isinstance(step, dict) or step.get("name") != step_name:
            continue
        argv = step.get("command") or []
        if not isinstance(argv, list):
            return {}
        parsed: dict[str, str] = {}
        i = 0
        while i < len(argv):
            token = argv[i]
            if isinstance(token, str) and token.startswith("--"):
                if i + 1 < len(argv) and not str(argv[i + 1]).startswith("--"):
                    parsed[token] = str(argv[i + 1])
                    i += 2
                    continue
                parsed[token] = "1"
            i += 1
        return parsed
    return {}


def _int_arg(step_args: dict[str, str], key: str, default: int) -> int:
    try:
        return int(step_args.get(key, default))
    except Exception:
        return int(default)


def _float_arg(step_args: dict[str, str], key: str, default: float) -> float:
    try:
        return float(step_args.get(key, default))
    except Exception:
        return float(default)


def build_strategy(strategy_name: str, fee_rate: float = 0.0, manifest_path: str | None = None) -> StrategyConfig:
    step_args = _manifest_step_args(manifest_path, "baseline")
    runtime_args = SimpleNamespace(
        top_n=_int_arg(step_args, "--top-n", 20),
        stop_loss_pct=_float_arg(step_args, "--stop-loss-pct", 0.12),
        trend_exit_ma=_int_arg(step_args, "--trend-exit-ma", 60),
        regime_ma_window=_int_arg(step_args, "--regime-ma-window", 200),
        regime_slope_window=_int_arg(step_args, "--regime-slope-window", 20),
        regime_breadth_threshold=_float_arg(step_args, "--regime-breadth-threshold", 0.55),
        vol_lookback=_int_arg(step_args, "--vol-lookback", 20),
        target_vol_annual=_float_arg(step_args, "--target-vol-annual", 0.20),
        max_weight=_float_arg(step_args, "--max-weight", 0.20),
        min_gross_exposure=_float_arg(step_args, "--min-gross-exposure", 0.50),
        score_top_k=_int_arg(step_args, "--score-top-k", 50),
        score_power=_float_arg(step_args, "--score-power", 1.5),
        allow_intraperiod_reentry=_int_arg(step_args, "--allow-intraperiod-reentry", 1),
        reentry_cooldown_days=_int_arg(step_args, "--reentry-cooldown-days", 0),
        osc_lookback=_int_arg(step_args, "--osc-lookback", 20),
        osc_z_entry=_float_arg(step_args, "--osc-z-entry", -1.5),
        osc_z_exit=_float_arg(step_args, "--osc-z-exit", -0.25),
        osc_z_stop=_float_arg(step_args, "--osc-z-stop", -2.5),
        osc_band_sigma=_float_arg(step_args, "--osc-band-sigma", 1.5),
        osc_band_break_sigma=_float_arg(step_args, "--osc-band-break-sigma", 2.0),
        osc_reentry_cooldown_days=_int_arg(step_args, "--osc-reentry-cooldown-days", 5),
        range_slope_threshold=_float_arg(step_args, "--range-slope-threshold", 0.015),
        range_dist_threshold=_float_arg(step_args, "--range-dist-threshold", 0.03),
        range_breakout_persistence_threshold=_float_arg(step_args, "--range-breakout-persistence-threshold", 0.35),
        range_breadth_tolerance=_float_arg(step_args, "--range-breadth-tolerance", 0.15),
        rotation_top_k=_int_arg(step_args, "--rotation-top-k", 5),
        rotation_tilt_strength=_float_arg(step_args, "--rotation-tilt-strength", 0.20),
        rotation_min_sleeve_weight=_float_arg(step_args, "--rotation-min-sleeve-weight", 0.25),
        risk_budget_lookback=_int_arg(step_args, "--risk-budget-lookback", 120),
        risk_budget_shrinkage=_float_arg(step_args, "--risk-budget-shrinkage", 0.35),
        risk_budget_iv_blend=_float_arg(step_args, "--risk-budget-iv-blend", 0.50),
    )
    base_kwargs = strategy_runtime_kwargs(
        runtime_args,
        fee_rate=fee_rate,
        use_regime_filter=bool(_int_arg(step_args, "--regime-filter", 1)),
    )
    base_kwargs["regime_off_exposure"] = _float_arg(step_args, "--regime-off-exposure", 0.40)
    baseline = {
        "Daily Top20": StrategyConfig(name="Daily Top20", rebalance="D", use_buffer=False, selection_mode="topn", entry_rank=20, exit_rank=25, **{**base_kwargs, "regime_off_exposure": 0.0}),
        "Weekly Top20": StrategyConfig(name="Weekly Top20", rebalance="W-FRI", use_buffer=False, selection_mode="topn", entry_rank=20, exit_rank=25, **{**base_kwargs, "regime_off_exposure": 0.0}),
        "Weekly Buffer 20/25": StrategyConfig(name="Weekly Buffer 20/25", rebalance="W-FRI", use_buffer=True, selection_mode="topn", entry_rank=20, exit_rank=25, **{**base_kwargs, "regime_off_exposure": 0.0}),
        "Weekly Score50 MADScale": StrategyConfig(name="Weekly Score50 MADScale", rebalance="W-FRI", use_buffer=False, selection_mode="score", entry_rank=20, exit_rank=25, **base_kwargs),
        "Biweekly Score50 MADScale": StrategyConfig(name="Biweekly Score50 MADScale", rebalance="W-2FRI", use_buffer=False, selection_mode="score", entry_rank=20, exit_rank=25, **base_kwargs),
        "Weekly Score50 RegimeState": StrategyConfig(name="Weekly Score50 RegimeState", rebalance="W-FRI", use_buffer=False, selection_mode="score", entry_rank=20, exit_rank=25, use_regime_state_model=True, **base_kwargs),
        "Weekly Score50 Rotation": StrategyConfig(name="Weekly Score50 Rotation", rebalance="W-FRI", use_buffer=False, selection_mode="score", entry_rank=20, exit_rank=25, use_regime_state_model=True, use_rotation_overlay=True, **base_kwargs),
        "Weekly ETF RiskBudget": StrategyConfig(name="Weekly ETF RiskBudget", rebalance="W-FRI", use_buffer=False, selection_mode="score", entry_rank=20, exit_rank=25, use_regime_state_model=True, use_etf_risk_budget=True, fixed_sleeve_weights={"stock": 0.0, "etf": 1.0}, **{**base_kwargs, "max_weight": max(float(base_kwargs["max_weight"]), 0.35)}),
        "Weekly ForeignFlow v2": StrategyConfig(name="Weekly ForeignFlow v2", rebalance="W-FRI", use_buffer=False, selection_mode="score", entry_rank=20, exit_rank=25, use_foreign_flow_model=True, flow_hold_buffer=10, flow_trend_ma=60, flow_foreign_ratio_cap=40.0, flow_foreign_ratio_penalty=0.50, **{**base_kwargs, "score_top_k": min(int(base_kwargs["score_top_k"]), int(base_kwargs["top_n_stock"]))}),
        "Weekly ForeignFlow v3": StrategyConfig(name="Weekly ForeignFlow v3", rebalance="W-FRI", use_buffer=False, selection_mode="score", entry_rank=20, exit_rank=25, use_foreign_flow_model=True, flow_model_version=3, flow_hold_buffer=10, flow_trend_ma=60, flow_foreign_ratio_cap=40.0, flow_foreign_ratio_penalty=0.50, **{**base_kwargs, "score_top_k": min(int(base_kwargs["score_top_k"]), int(base_kwargs["top_n_stock"]))}),
        "Weekly QualityProfitability MVP": StrategyConfig(name="Weekly QualityProfitability MVP", rebalance="W-FRI", use_buffer=False, selection_mode="score", entry_rank=20, exit_rank=25, use_quality_profitability_model=True, fixed_sleeve_weights={"stock": 1.0, "etf": 0.0}, **{**base_kwargs, "score_top_k": min(int(base_kwargs["score_top_k"]), int(base_kwargs["top_n_stock"]))}),
        "Weekly Score50 RangeOsc": StrategyConfig(name="Weekly Score50 RangeOsc", rebalance="W-FRI", use_buffer=False, selection_mode="score", entry_rank=20, exit_rank=25, use_regime_state_model=True, enable_oscillation_long=True, **base_kwargs),
        "Biweekly Score50 RegimeState": StrategyConfig(name="Biweekly Score50 RegimeState", rebalance="W-2FRI", use_buffer=False, selection_mode="score", entry_rank=20, exit_rank=25, use_regime_state_model=True, **base_kwargs),
        "Biweekly Score50 Rotation": StrategyConfig(name="Biweekly Score50 Rotation", rebalance="W-2FRI", use_buffer=False, selection_mode="score", entry_rank=20, exit_rank=25, use_regime_state_model=True, use_rotation_overlay=True, **base_kwargs),
        "Biweekly ETF RiskBudget": StrategyConfig(name="Biweekly ETF RiskBudget", rebalance="W-2FRI", use_buffer=False, selection_mode="score", entry_rank=20, exit_rank=25, use_regime_state_model=True, use_etf_risk_budget=True, fixed_sleeve_weights={"stock": 0.0, "etf": 1.0}, **{**base_kwargs, "max_weight": max(float(base_kwargs["max_weight"]), 0.35)}),
        "Biweekly Score50 RangeOsc": StrategyConfig(name="Biweekly Score50 RangeOsc", rebalance="W-2FRI", use_buffer=False, selection_mode="score", entry_rank=20, exit_rank=25, use_regime_state_model=True, enable_oscillation_long=True, **base_kwargs),
    }
    if strategy_name in baseline:
        return baseline[strategy_name]

    m = SCORE_NAME_RE.match(strategy_name)
    if m:
        n = int(m.group("n"))
        power = float(m.group("power"))
        roe = float(m.group("roe"))
        return StrategyConfig(
            name=strategy_name,
            rebalance="W-FRI",
            top_n_stock=base_kwargs["top_n_stock"],
            top_n_etf=base_kwargs["top_n_etf"],
            fee_rate=fee_rate,
            use_buffer=False,
            entry_rank=20,
            exit_rank=25,
            use_regime_filter=base_kwargs["use_regime_filter"],
            stop_loss_pct=base_kwargs["stop_loss_pct"],
            trend_exit_ma=base_kwargs["trend_exit_ma"],
            regime_ma_window=base_kwargs["regime_ma_window"],
            regime_slope_window=base_kwargs["regime_slope_window"],
            regime_breadth_threshold=base_kwargs["regime_breadth_threshold"],
            vol_lookback=base_kwargs["vol_lookback"],
            target_vol_annual=base_kwargs["target_vol_annual"],
            max_weight=base_kwargs["max_weight"],
            min_gross_exposure=base_kwargs["min_gross_exposure"],
            selection_mode="score",
            score_top_k=max(1, n // 2),
            score_power=power,
            regime_off_exposure=roe,
            allow_intraperiod_reentry=base_kwargs["allow_intraperiod_reentry"],
            reentry_cooldown_days=base_kwargs["reentry_cooldown_days"],
            osc_lookback=base_kwargs["osc_lookback"],
            osc_z_entry=base_kwargs["osc_z_entry"],
            osc_z_exit=base_kwargs["osc_z_exit"],
            osc_z_stop=base_kwargs["osc_z_stop"],
            osc_band_sigma=base_kwargs["osc_band_sigma"],
            osc_band_break_sigma=base_kwargs["osc_band_break_sigma"],
            osc_reentry_cooldown_days=base_kwargs["osc_reentry_cooldown_days"],
            range_slope_threshold=base_kwargs["range_slope_threshold"],
            range_dist_threshold=base_kwargs["range_dist_threshold"],
            range_breakout_persistence_threshold=base_kwargs["range_breakout_persistence_threshold"],
            range_breadth_tolerance=base_kwargs["range_breadth_tolerance"],
        )
    raise ValueError(f"Unsupported strategy name: {strategy_name}")


def _regime_frame(cs: pd.DataFrame, stg: StrategyConfig) -> pd.DataFrame:
    return compute_regime_state(cs, stg)


def _apply_decision(
    decision_dt: pd.Timestamp,
    cs: pd.DataFrame,
    ce: pd.DataFrame,
    rs: pd.DataFrame,
    re: pd.DataFrame,
    fs: Dict[str, pd.DataFrame],
    fe: Dict[str, pd.DataFrame],
    regime_frame: pd.DataFrame,
    reb_dates: set[pd.Timestamp],
    stg: StrategyConfig,
    hold_s: list[str],
    hold_e: list[str],
    w_now: dict[str, float],
    entry_px: dict[str, float],
    entry_reason: dict[str, str],
    cooldown_left: dict[str, int],
    universe_s: pd.DataFrame | None = None,
    universe_e: pd.DataFrame | None = None,
    flow_score: pd.DataFrame | None = None,
    quality_mats: Dict[str, pd.DataFrame] | None = None,
) -> Tuple[list[str], list[str], dict[str, float], dict[str, float], dict[str, str], dict[str, int], str, pd.DataFrame, pd.DataFrame]:
    scheduled_rebalance = decision_dt in reb_dates
    rebalance_now = scheduled_rebalance

    risk_on = regime_frame["RiskOn"]
    regime_state = regime_frame["RegimeState"]
    ma_trend_s = cs.rolling(stg.trend_exit_ma, min_periods=stg.trend_exit_ma).mean() if stg.trend_exit_ma > 0 else pd.DataFrame(index=cs.index, columns=cs.columns)
    ma_trend_e = ce.rolling(stg.trend_exit_ma, min_periods=stg.trend_exit_ma).mean() if stg.trend_exit_ma > 0 else pd.DataFrame(index=ce.index, columns=ce.columns)

    if hold_s or hold_e:
        keep_s: list[str] = []
        for t in hold_s:
            px = cs.at[decision_dt, t] if t in cs.columns else np.nan
            if pd.isna(px):
                continue
            stop_hit = stg.stop_loss_pct > 0 and t in entry_px and px <= entry_px[t] * (1.0 - stg.stop_loss_pct)
            trend_hit = False
            if stg.trend_exit_ma > 0:
                ma = ma_trend_s.at[decision_dt, t] if t in ma_trend_s.columns else np.nan
                if pd.notna(ma):
                    trend_hit = px < ma
            osc_take_profit = False
            osc_invalid = False
            if entry_reason.get(t) == "osc":
                osc_z = fs["osc_z"].at[decision_dt, t] if t in fs["osc_z"].columns else np.nan
                osc_mean = fs["osc_mean"].at[decision_dt, t] if t in fs["osc_mean"].columns else np.nan
                osc_break_persist = fs["osc_break_persist"].at[decision_dt, t] if t in fs["osc_break_persist"].columns else np.nan
                osc_take_profit = pd.notna(osc_z) and float(osc_z) >= stg.osc_z_exit
                if pd.notna(osc_mean):
                    osc_take_profit = bool(osc_take_profit or px >= osc_mean)
                osc_invalid = (
                    (pd.notna(osc_z) and float(osc_z) <= stg.osc_z_stop)
                    or (pd.notna(osc_break_persist) and float(osc_break_persist) >= 2.0)
                    or (stg.use_regime_state_model and str(regime_state.get(decision_dt, "TRANSITION")) != "RANGE")
                )
            if stop_hit or trend_hit or osc_take_profit or osc_invalid:
                if entry_reason.get(t) == "osc" and (stop_hit or trend_hit or osc_invalid):
                    cd_days = stg.osc_reentry_cooldown_days
                else:
                    cd_days = stg.reentry_cooldown_days
                if cd_days > 0:
                    cooldown_left[t] = int(cd_days)
                entry_reason.pop(t, None)
            else:
                keep_s.append(t)
        keep_e: list[str] = []
        for t in hold_e:
            px = ce.at[decision_dt, t] if t in ce.columns else np.nan
            if pd.isna(px):
                continue
            stop_hit = stg.stop_loss_pct > 0 and t in entry_px and px <= entry_px[t] * (1.0 - stg.stop_loss_pct)
            trend_hit = False
            if stg.trend_exit_ma > 0:
                ma = ma_trend_e.at[decision_dt, t] if t in ma_trend_e.columns else np.nan
                if pd.notna(ma):
                    trend_hit = px < ma
            if (stop_hit or trend_hit) and stg.reentry_cooldown_days > 0:
                cooldown_left[t] = int(stg.reentry_cooldown_days)
                entry_reason.pop(t, None)
            elif not stop_hit and not trend_hit:
                keep_e.append(t)
        if keep_s != hold_s or keep_e != hold_e:
            hold_s, hold_e = keep_s, keep_e
            rebalance_now = True

    regime_on = bool(risk_on.get(decision_dt, False))
    regime_name = str(regime_state.get(decision_dt, "TRANSITION"))
    regime_target_exposure = 1.0
    if stg.use_regime_filter and not regime_on:
        regime_target_exposure = float(np.clip(stg.regime_off_exposure, 0.0, 1.0))

    do_reentry = scheduled_rebalance or stg.allow_intraperiod_reentry
    rank_s = rank_at(fs, decision_dt, universe_s) if do_reentry else pd.DataFrame()
    rank_e = rank_at(fe, decision_dt, universe_e) if do_reentry else pd.DataFrame()
    rank_s_use = rank_s
    osc_rank_s = pd.DataFrame()
    if do_reentry and stg.enable_oscillation_long and regime_name == "RANGE":
        osc_rank_s = oscillation_candidates_at(fs, decision_dt, stg, universe_s)

    if regime_target_exposure <= 0:
        hold_s, hold_e = [], []
    elif do_reentry and stg.use_etf_risk_budget:
        hold_s = []
        if universe_e is not None and decision_dt in universe_e.index:
            eligible_etfs = list(universe_e.columns[universe_e.loc[decision_dt].fillna(False)])
        else:
            eligible_etfs = list(ce.columns)
        if stg.top_n_etf > 0:
            eligible_etfs = eligible_etfs[: int(stg.top_n_etf)]
        hold_e = [t for t in eligible_etfs if cooldown_left.get(t, 0) <= 0]
    elif do_reentry and stg.use_foreign_flow_model:
        hold_e = []
        rank_s_use = rank_flow_at(
            fs,
            flow_score if flow_score is not None else pd.DataFrame(),
            cs,
            decision_dt,
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
            decision_dt,
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
            rank_s_use = _merge_rank_frames(
                rank_s,
                preserved_hold_s,
                new_osc,
                max(1, int(stg.score_top_k if stg.selection_mode == "score" else stg.top_n_stock)),
            )
            cand_s = list(rank_s_use.index)
        elif regime_name in {"DOWNTREND", "TRANSITION"} and stg.use_regime_state_model:
            preserved_hold_s = [t for t in hold_s if t in rank_s.index]
            rank_s_use = rank_s.loc[preserved_hold_s] if preserved_hold_s else rank_s.iloc[0:0]
            cand_s = list(rank_s_use.index)
        else:
            cand_s = [t for t in list(rank_s.index) if cooldown_left.get(t, 0) <= 0]
        cand_e = [t for t in list(rank_e.index) if cooldown_left.get(t, 0) <= 0]
        if stg.selection_mode == "score":
            hold_s = cand_s[: max(1, int(stg.score_top_k))]
            hold_e = cand_e[: max(1, int(stg.score_top_k))]
        else:
            hold_s = select_buffer(cand_s, hold_s, stg.top_n_stock, stg.use_buffer, stg.entry_rank, stg.exit_rank)
            hold_e = select_buffer(cand_e, hold_e, stg.top_n_etf, stg.use_buffer, stg.entry_rank, stg.exit_rank)

    ret_s = rs.loc[:decision_dt].tail(stg.vol_lookback)
    ret_e = re.loc[:decision_dt].tail(stg.vol_lookback)
    if stg.use_etf_risk_budget:
        w_s = {}
        w_e = _risk_budget_weights(re.loc[:decision_dt].tail(max(20, int(stg.risk_budget_lookback))), hold_e, stg)
    elif stg.use_foreign_flow_model:
        w_s = {ticker: 1.0 / len(hold_s) for ticker in hold_s} if hold_s else {}
        w_e = {}
    elif stg.selection_mode == "score":
        w_s = _score_weights_from_rank(rank_s_use.loc[rank_s_use.index.intersection(hold_s)], stg)
        w_e = _score_weights_from_rank(rank_e.loc[rank_e.index.intersection(hold_e)], stg)
    else:
        w_s = _inverse_vol_weights(ret_s, hold_s)
        w_e = _inverse_vol_weights(ret_e, hold_e)

    stock_sleeve = 0.5
    etf_sleeve = 0.5
    if stg.use_rotation_overlay and w_s and w_e:
        _, stock_sleeve, etf_sleeve = _rotation_signal_from_ranks(rank_s_use, rank_e, stg)
    w_tar: dict[str, float] = {}
    if w_s and w_e:
        w_tar.update({k: v * stock_sleeve for k, v in w_s.items()})
        w_tar.update({k: v * etf_sleeve for k, v in w_e.items()})
    elif w_s:
        w_tar.update(w_s)
    elif w_e:
        w_tar.update(w_e)

    w_tar = _cap_weights_to_target(w_tar, stg.max_weight, regime_target_exposure)
    removed = set(w_now) - set(w_tar)
    added = set(w_tar) - set(w_now)
    for t in removed:
        entry_px.pop(t, None)
        entry_reason.pop(t, None)
    for t in added:
        px = cs.at[decision_dt, t] if t in cs.columns else ce.at[decision_dt, t] if t in ce.columns else np.nan
        if pd.notna(px):
            entry_px[t] = float(px)
        entry_reason[t] = "osc" if bool(stg.enable_oscillation_long and regime_name == "RANGE" and t in osc_rank_s.index) else "momo"
    return hold_s, hold_e, w_tar, entry_px, entry_reason, cooldown_left, regime_name, rank_s_use, rank_e


def compute_target_portfolio(
    base: str,
    strategy_name: str,
    min_common_dates: int = 180,
    as_of_date: str | None = None,
    manifest_path: str | None = None,
    max_files: int = 0,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if is_hybrid_strategy_name(strategy_name):
        spec = HYBRID_STRATEGY_COMPONENTS[strategy_name]
        component_frames: list[pd.DataFrame] = []
        component_regimes: list[str] = []
        latest_date = ""
        as_of_value = ""
        for component_name, weight in spec.items():
            component_df, component_meta = compute_target_portfolio(
                base=base,
                strategy_name=component_name,
                min_common_dates=min_common_dates,
                as_of_date=as_of_date,
                manifest_path=manifest_path,
                max_files=max_files,
            )
            component_regimes.append(str(component_meta.get("RegimeState", "")))
            latest_date = str(component_meta.get("LatestDate", latest_date) or latest_date)
            as_of_value = str(component_meta.get("AsOfDate", as_of_value) or as_of_value)
            tmp = component_df.copy()
            if tmp.empty:
                continue
            tmp["WeightedTargetWeight"] = tmp["TargetWeight"].astype(float) * float(weight)
            tmp["WeightedSignalRank"] = pd.to_numeric(tmp.get("SignalRank", np.nan), errors="coerce") * float(weight)
            tmp["WeightedScore"] = pd.to_numeric(tmp.get("Score", np.nan), errors="coerce") * float(weight)
            tmp["SignalWeight"] = pd.to_numeric(tmp.get("SignalRank", np.nan), errors="coerce").notna().astype(float) * float(weight)
            tmp["ScoreWeight"] = pd.to_numeric(tmp.get("Score", np.nan), errors="coerce").notna().astype(float) * float(weight)
            component_frames.append(tmp)

        if not component_frames:
            empty = pd.DataFrame(columns=["AsOfDate", "Code", "Name", "AssetType", "TargetWeight", "CurrentPrice", "SignalRank", "Score", "RegimeState", "Notes"])
            meta = {
                "Strategy": strategy_name,
                "AsOfDate": as_of_value,
                "RegimeState": component_regimes[0] if component_regimes else "",
                "WeightSum": 0.0,
                "HoldingsCount": 0,
                "LatestDate": latest_date,
            }
            return empty, meta

        combined = pd.concat(component_frames, ignore_index=True)
        grouped = (
            combined.groupby(["Code", "AssetType"], as_index=False)
            .agg(
                {
                    "Name": "first",
                    "CurrentPrice": "last",
                    "WeightedTargetWeight": "sum",
                    "WeightedSignalRank": "sum",
                    "WeightedScore": "sum",
                    "SignalWeight": "sum",
                    "ScoreWeight": "sum",
                }
            )
            .rename(columns={"WeightedTargetWeight": "TargetWeight"})
        )
        grouped["SignalRank"] = grouped["WeightedSignalRank"] / grouped["SignalWeight"].replace(0.0, np.nan)
        grouped["Score"] = grouped["WeightedScore"] / grouped["ScoreWeight"].replace(0.0, np.nan)
        grouped["AsOfDate"] = as_of_value
        grouped["RegimeState"] = component_regimes[0] if len(set(component_regimes)) <= 1 else "MIXED"
        grouped["Notes"] = "hybrid_target"
        grouped = grouped.drop(columns=["WeightedSignalRank", "WeightedScore", "SignalWeight", "ScoreWeight"])
        grouped = grouped[grouped["TargetWeight"] > 1e-8].copy()
        weight_sum = float(grouped["TargetWeight"].sum()) if not grouped.empty else 0.0
        if weight_sum > 0:
            grouped["TargetWeight"] = grouped["TargetWeight"] / weight_sum
        grouped = grouped.sort_values(["TargetWeight", "Code"], ascending=[False, True]).reset_index(drop=True)
        meta = {
            "Strategy": strategy_name,
            "AsOfDate": as_of_value,
            "RegimeState": grouped["RegimeState"].iloc[0] if not grouped.empty else (component_regimes[0] if component_regimes else ""),
            "WeightSum": float(grouped["TargetWeight"].sum()) if not grouped.empty else 0.0,
            "HoldingsCount": int(len(grouped)),
            "LatestDate": latest_date,
        }
        return grouped[["AsOfDate", "Code", "Name", "AssetType", "TargetWeight", "CurrentPrice", "SignalRank", "Score", "RegimeState", "Notes"]], meta

    stg = build_strategy(strategy_name, fee_rate=0.0, manifest_path=manifest_path)
    close_s, value_s = build_market_matrices(base, "stock", max_files)
    close_e, value_e = build_market_matrices(base, "etf", max_files)
    fixed_sleeves = dict(getattr(stg, "fixed_sleeve_weights", {}) or {})
    stock_disabled = float(fixed_sleeves.get("stock", 1.0)) <= 1e-12
    etf_disabled = float(fixed_sleeves.get("etf", 1.0)) <= 1e-12

    if close_s.empty and not close_e.empty and stock_disabled:
        dates = sorted(close_e.index)
    elif close_e.empty and not close_s.empty and etf_disabled:
        dates = sorted(close_s.index)
    else:
        dates = sorted(set(close_s.index).intersection(set(close_e.index)))
    if len(dates) < min_common_dates:
        raise RuntimeError(f"Not enough common dates. Need at least {min_common_dates}.")
    dates = pd.DatetimeIndex(dates)
    as_of_ts = parse_as_of_date(as_of_date)
    if as_of_ts is not None:
        dates = dates[dates <= as_of_ts]
        if len(dates) < min_common_dates:
            raise RuntimeError(f"Not enough common dates through {as_of_date}.")
    as_of_ts = dates[-1]

    cs = close_s.loc[dates] if not close_s.empty else pd.DataFrame(index=dates)
    ce = close_e.loc[dates] if not close_e.empty else pd.DataFrame(index=dates)
    rs, re = cs.pct_change(fill_method=None).fillna(0.0), ce.pct_change(fill_method=None).fillna(0.0)
    fs, fe = features(cs, stg), features(ce, stg)
    regime_input = cs
    if regime_input.empty and not ce.empty and stock_disabled:
        regime_input = ce
    regime_frame = _regime_frame(regime_input, stg)
    universe_s = None
    if stg.use_point_in_time_universe and not cs.empty:
        universe_s = compute_point_in_time_universe(cs, value_s.loc[dates, cs.columns], "stock", stg)
    universe_e = None
    if stg.use_point_in_time_universe and not ce.empty:
        universe_e = compute_point_in_time_universe(ce, value_e.loc[dates, ce.columns], "etf", stg)
    flow_score = None
    if stg.use_foreign_flow_model:
        flow_mats = build_flow_matrices(default_flow_base(), market="stock", max_files=max_files)
        flow_fn = compute_flow_score_v3 if int(getattr(stg, "flow_model_version", 2)) >= 3 else compute_flow_score
        flow_score = flow_fn(
            cs,
            value_s.loc[dates, cs.columns],
            flow_mats,
            foreign_ratio_cap=stg.flow_foreign_ratio_cap,
            foreign_ratio_penalty=stg.flow_foreign_ratio_penalty,
        ).reindex(index=dates, columns=cs.columns)
    quality_mats = build_quality_matrices(default_quality_base(), cs.index, list(cs.columns)) if stg.use_quality_profitability_model else None
    reb_dates = set(rebalance_dates(dates, stg.rebalance))

    hold_s: list[str] = []
    hold_e: list[str] = []
    w_now: dict[str, float] = {}
    entry_px: dict[str, float] = {}
    entry_reason: dict[str, str] = {}
    cooldown_left: dict[str, int] = {}

    for i in range(1, len(dates)):
        prev_dt = dates[i - 1]
        if cooldown_left:
            for t in list(cooldown_left.keys()):
                cooldown_left[t] -= 1
                if cooldown_left[t] <= 0:
                    cooldown_left.pop(t, None)
        hold_s, hold_e, w_now, entry_px, entry_reason, cooldown_left, _, _, _ = _apply_decision(
            prev_dt, cs, ce, rs, re, fs, fe, regime_frame, reb_dates, stg,
            hold_s, hold_e, w_now, entry_px, entry_reason, cooldown_left, universe_s, universe_e, flow_score, quality_mats,
        )

    hold_s, hold_e, w_final, entry_px, entry_reason, cooldown_left, regime_state, rank_s, rank_e = _apply_decision(
        as_of_ts, cs, ce, rs, re, fs, fe, regime_frame, reb_dates, stg,
        hold_s, hold_e, w_now, entry_px, entry_reason, cooldown_left, universe_s, universe_e, flow_score, quality_mats,
    )

    rows: list[dict[str, Any]] = []
    combined_rank = pd.concat([rank_s, rank_e], axis=0) if not rank_s.empty or not rank_e.empty else pd.DataFrame()
    rank_pos = {ticker: idx + 1 for idx, ticker in enumerate(combined_rank.index.tolist())}
    for ticker, weight in sorted(w_final.items(), key=lambda kv: (-kv[1], kv[0])):
        asset_type = "STOCK" if ticker.startswith("S_") else "ETF"
        current_price = cs.at[as_of_ts, ticker] if ticker in cs.columns else ce.at[as_of_ts, ticker] if ticker in ce.columns else np.nan
        rank_row = combined_rank.loc[ticker] if ticker in combined_rank.index else pd.Series(dtype=float)
        rows.append(
            {
                "AsOfDate": as_of_ts.strftime("%Y-%m-%d"),
                "Code": ticker.split("_", 1)[1] if "_" in ticker else ticker,
                "Name": "",
                "AssetType": asset_type,
                "TargetWeight": float(weight),
                "CurrentPrice": float(current_price) if pd.notna(current_price) else np.nan,
                "SignalRank": rank_pos.get(ticker, np.nan),
                "Score": float(rank_row.get("buy_score", np.nan)) if not rank_row.empty else np.nan,
                "RegimeState": regime_state,
                "Notes": "current_target",
            }
        )

    out = pd.DataFrame(rows)
    meta = {
        "Strategy": strategy_name,
        "AsOfDate": as_of_ts.strftime("%Y-%m-%d"),
        "RegimeState": regime_state,
        "WeightSum": float(out["TargetWeight"].sum()) if not out.empty else 0.0,
        "HoldingsCount": int(len(out)),
        "LatestDate": as_of_ts.strftime("%Y-%m-%d"),
    }
    return out, meta


def get_previous_row_run_id(df: pd.DataFrame) -> str | None:
    if df.empty or "RunId" not in df.columns:
        return None
    vals = df["RunId"].dropna().astype(str)
    return str(vals.iloc[0]) if not vals.empty else None
