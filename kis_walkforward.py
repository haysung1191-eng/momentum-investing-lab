import argparse
import itertools
import sys
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

import config
from kis_backtest_from_prices import (
    HYBRID_STRATEGY_COMPONENTS,
    StrategyConfig,
    blend_strategy_results,
    build_market_matrices,
    default_flow_base,
    default_quality_base,
    run_one,
    strategy_runtime_kwargs,
    write_csv_any,
)
from kis_flow_data import build_flow_matrices
from kis_quality_data import build_quality_matrices

try:
    from tqdm.auto import tqdm
except Exception:  # pragma: no cover
    def tqdm(x, **kwargs):  # type: ignore
        return x


def progress(iterable, **kwargs):
    disable = kwargs.pop("disable", None)
    if disable is None:
        disable = not bool(getattr(sys.stdout, "isatty", lambda: False)())
    return tqdm(iterable, disable=disable, **kwargs)


@dataclass
class Combo:
    n: int
    score_power: float
    regime_off_exposure: float

    @property
    def name(self) -> str:
        return f"ScoreN{self.n}_P{self.score_power:.1f}_ROE{self.regime_off_exposure:.1f}"


def make_score_strategy(args: argparse.Namespace, combo: Combo, fee_rate: float) -> StrategyConfig:
    k_per_sleeve = max(1, int(combo.n) // 2)
    return StrategyConfig(
        name=combo.name,
        rebalance=args.rebalance,
        top_n_stock=args.top_n,
        top_n_etf=args.top_n,
        fee_rate=fee_rate,
        use_buffer=False,
        entry_rank=20,
        exit_rank=25,
        use_regime_filter=bool(args.regime_filter),
        stop_loss_pct=args.stop_loss_pct,
        trend_exit_ma=args.trend_exit_ma,
        regime_ma_window=args.regime_ma_window,
        regime_slope_window=args.regime_slope_window,
        regime_breadth_threshold=args.regime_breadth_threshold,
        vol_lookback=args.vol_lookback,
        target_vol_annual=args.target_vol_annual,
        max_weight=args.max_weight,
        min_gross_exposure=args.min_gross_exposure,
        selection_mode="score",
        score_top_k=k_per_sleeve,
        score_power=combo.score_power,
        regime_off_exposure=combo.regime_off_exposure,
        allow_intraperiod_reentry=bool(args.allow_intraperiod_reentry),
        reentry_cooldown_days=args.reentry_cooldown_days,
    )


def make_benchmark(args: argparse.Namespace, fee_rate: float) -> StrategyConfig:
    return StrategyConfig(
        name="Benchmark Weekly Top20",
        rebalance="W-FRI",
        top_n_stock=args.top_n,
        top_n_etf=args.top_n,
        fee_rate=fee_rate,
        use_buffer=False,
        entry_rank=20,
        exit_rank=25,
        use_regime_filter=bool(args.regime_filter),
        stop_loss_pct=args.stop_loss_pct,
        trend_exit_ma=args.trend_exit_ma,
        regime_ma_window=args.regime_ma_window,
        regime_slope_window=args.regime_slope_window,
        regime_breadth_threshold=args.regime_breadth_threshold,
        vol_lookback=args.vol_lookback,
        target_vol_annual=args.target_vol_annual,
        max_weight=args.max_weight,
        min_gross_exposure=args.min_gross_exposure,
        selection_mode="topn",
        score_top_k=50,
        score_power=1.5,
        regime_off_exposure=0.4,
        allow_intraperiod_reentry=bool(args.allow_intraperiod_reentry),
        reentry_cooldown_days=args.reentry_cooldown_days,
    )


def build_named_strategies(args: argparse.Namespace, fee_rate: float) -> List[StrategyConfig]:
    use_regime = bool(args.regime_filter)
    base_kwargs = strategy_runtime_kwargs(args, fee_rate=fee_rate, use_regime_filter=use_regime)
    base_kwargs["regime_off_exposure"] = args.regime_off_exposure
    return [
        StrategyConfig(
            name="Daily Top20",
            rebalance="D",
            use_buffer=False,
            selection_mode="topn",
            entry_rank=20,
            exit_rank=25,
            **base_kwargs,
        ),
        StrategyConfig(
            name="Weekly Top20",
            rebalance="W-FRI",
            use_buffer=False,
            selection_mode="topn",
            entry_rank=20,
            exit_rank=25,
            **base_kwargs,
        ),
        StrategyConfig(
            name="Weekly Buffer 20/25",
            rebalance="W-FRI",
            use_buffer=True,
            selection_mode="topn",
            entry_rank=20,
            exit_rank=25,
            **base_kwargs,
        ),
        StrategyConfig(
            name="Weekly Score50 MADScale",
            rebalance="W-FRI",
            use_buffer=False,
            selection_mode="score",
            entry_rank=20,
            exit_rank=25,
            **base_kwargs,
        ),
        StrategyConfig(
            name="Biweekly Score50 MADScale",
            rebalance="W-2FRI",
            use_buffer=False,
            selection_mode="score",
            entry_rank=20,
            exit_rank=25,
            **base_kwargs,
        ),
        StrategyConfig(
            name="Weekly Score50 RegimeState",
            rebalance="W-FRI",
            use_buffer=False,
            selection_mode="score",
            entry_rank=20,
            exit_rank=25,
            use_regime_state_model=True,
            **base_kwargs,
        ),
        StrategyConfig(
            name="Weekly Score50 Rotation",
            rebalance="W-FRI",
            use_buffer=False,
            selection_mode="score",
            entry_rank=20,
            exit_rank=25,
            use_regime_state_model=True,
            use_rotation_overlay=True,
            **base_kwargs,
        ),
        StrategyConfig(
            name="Weekly ETF RiskBudget",
            rebalance="W-FRI",
            use_buffer=False,
            selection_mode="score",
            entry_rank=20,
            exit_rank=25,
            use_regime_state_model=True,
            use_etf_risk_budget=True,
            fixed_sleeve_weights={"stock": 0.0, "etf": 1.0},
            **{**base_kwargs, "max_weight": max(float(args.max_weight), 0.35)},
        ),
        StrategyConfig(
            name="Weekly ForeignFlow v2",
            rebalance="W-FRI",
            use_buffer=False,
            selection_mode="score",
            entry_rank=20,
            exit_rank=25,
            use_foreign_flow_model=True,
            flow_hold_buffer=10,
            flow_trend_ma=60,
            flow_foreign_ratio_cap=40.0,
            flow_foreign_ratio_penalty=0.50,
            **{**base_kwargs, "score_top_k": min(int(args.score_top_k), int(args.top_n))},
        ),
        StrategyConfig(
            name="Weekly ForeignFlow v3",
            rebalance="W-FRI",
            use_buffer=False,
            selection_mode="score",
            entry_rank=20,
            exit_rank=25,
            use_foreign_flow_model=True,
            flow_model_version=3,
            flow_hold_buffer=10,
            flow_trend_ma=60,
            flow_foreign_ratio_cap=40.0,
            flow_foreign_ratio_penalty=0.50,
            **{**base_kwargs, "score_top_k": min(int(args.score_top_k), int(args.top_n))},
        ),
        StrategyConfig(
            name="Weekly QualityProfitability MVP",
            rebalance="W-FRI",
            use_buffer=False,
            selection_mode="score",
            entry_rank=20,
            exit_rank=25,
            use_quality_profitability_model=True,
            fixed_sleeve_weights={"stock": 1.0, "etf": 0.0},
            **{**base_kwargs, "score_top_k": min(int(args.score_top_k), int(args.top_n))},
        ),
        StrategyConfig(
            name="Weekly Score50 RangeOsc",
            rebalance="W-FRI",
            use_buffer=False,
            selection_mode="score",
            entry_rank=20,
            exit_rank=25,
            use_regime_state_model=True,
            enable_oscillation_long=True,
            **base_kwargs,
        ),
        StrategyConfig(
            name="Biweekly Score50 RegimeState",
            rebalance="W-2FRI",
            use_buffer=False,
            selection_mode="score",
            entry_rank=20,
            exit_rank=25,
            use_regime_state_model=True,
            **base_kwargs,
        ),
        StrategyConfig(
            name="Biweekly Score50 Rotation",
            rebalance="W-2FRI",
            use_buffer=False,
            selection_mode="score",
            entry_rank=20,
            exit_rank=25,
            use_regime_state_model=True,
            use_rotation_overlay=True,
            **base_kwargs,
        ),
        StrategyConfig(
            name="Biweekly ETF RiskBudget",
            rebalance="W-2FRI",
            use_buffer=False,
            selection_mode="score",
            entry_rank=20,
            exit_rank=25,
            use_regime_state_model=True,
            use_etf_risk_budget=True,
            fixed_sleeve_weights={"stock": 0.0, "etf": 1.0},
            **{**base_kwargs, "max_weight": max(float(args.max_weight), 0.35)},
        ),
        StrategyConfig(
            name="Biweekly Score50 RangeOsc",
            rebalance="W-2FRI",
            use_buffer=False,
            selection_mode="score",
            entry_rank=20,
            exit_rank=25,
            use_regime_state_model=True,
            enable_oscillation_long=True,
            **base_kwargs,
        ),
    ]


def build_windows(index: pd.DatetimeIndex, train_years: int, test_years: int, step_years: int) -> List[Tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp, pd.Timestamp]]:
    windows = []
    min_dt = pd.Timestamp(index.min()).normalize()
    max_dt = pd.Timestamp(index.max()).normalize()
    cur = min_dt
    while True:
        train_start = cur
        train_end = (train_start + pd.DateOffset(years=train_years) - pd.Timedelta(days=1)).normalize()
        test_start = train_end + pd.Timedelta(days=1)
        test_end = (test_start + pd.DateOffset(years=test_years) - pd.Timedelta(days=1)).normalize()
        if test_end > max_dt:
            break
        windows.append((train_start, train_end, test_start, test_end))
        cur = (cur + pd.DateOffset(years=step_years)).normalize()
    return windows


def choose_feasible_window_params(
    index: pd.DatetimeIndex,
    requested_train: int,
    requested_test: int,
    requested_step: int,
    min_oos_windows: int,
) -> Tuple[int, int, int, bool]:
    requested = build_windows(index, requested_train, requested_test, requested_step)
    if len(requested) >= min_oos_windows:
        return requested_train, requested_test, requested_step, False

    span_years = max(float((pd.Timestamp(index.max()) - pd.Timestamp(index.min())).days) / 365.25, 0.0)
    max_year_int = max(1, int(span_years))
    max_train = min(max_year_int, max(1, requested_train))
    max_test = min(max_year_int, max(1, requested_test))
    max_step = max(1, requested_step)

    candidates: List[Tuple[int, int, int, int]] = []
    for train in range(max(1, requested_train), 0, -1):
        for test in range(max(1, requested_test), 0, -1):
            for step in range(max(1, requested_step), 0, -1):
                wins = build_windows(index, train, test, step)
                if len(wins) >= min_oos_windows:
                    candidates.append((train, test, step, len(wins)))
    if not candidates:
        for train in range(max_train, 0, -1):
            for test in range(max_test, 0, -1):
                for step in range(max_step, 0, -1):
                    wins = build_windows(index, train, test, step)
                    if wins:
                        candidates.append((train, test, step, len(wins)))
    if not candidates:
        return requested_train, requested_test, requested_step, False

    # Prefer longer train+test span, then more OOS windows, then longer train, then longer test, then smaller step.
    best = sorted(candidates, key=lambda x: (x[0] + x[1], x[3], x[0], x[1], -x[2]), reverse=True)[0]
    return best[0], best[1], best[2], True


def slice_period(close: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return close.loc[(close.index >= start) & (close.index <= end)]


def _window_metrics(out: pd.DataFrame) -> Dict[str, float]:
    if out is None or out.empty or len(out) < 2:
        return {"CAGR": 0.0, "MDD": 0.0, "Sharpe": 0.0}
    r = out["daily_return"].astype(float).fillna(0.0)
    nav = (1.0 + r).cumprod()
    years = max((out.index[-1] - out.index[0]).days / 365.25, 1e-9)
    cagr = float(nav.iloc[-1] ** (1 / years) - 1)
    hwm = nav.cummax()
    mdd = float((nav / hwm - 1).min())
    sr = float((r.mean() / (r.std(ddof=0) + 1e-12)) * np.sqrt(252))
    return {"CAGR": cagr, "MDD": mdd, "Sharpe": sr}


def run_test_with_warmup(
    close_s_all: pd.DataFrame,
    close_e_all: pd.DataFrame,
    value_s_all: pd.DataFrame,
    value_e_all: pd.DataFrame,
    flow_mats: Dict[str, pd.DataFrame] | None,
    quality_mats: Dict[str, pd.DataFrame] | None,
    test_start: pd.Timestamp,
    test_end: pd.Timestamp,
    stg: StrategyConfig,
    min_common_dates: int,
    warmup_days: int = 260,
) -> Tuple[Dict[str, float], Dict[str, float]]:
    idx_all = close_s_all.index.intersection(close_e_all.index).sort_values()
    if len(idx_all) < min_common_dates:
        raise RuntimeError("Not enough common dates for warmup evaluation.")

    start_pos = int(np.searchsorted(idx_all.values, np.datetime64(test_start), side="left"))
    if start_pos >= len(idx_all):
        raise RuntimeError("Test start is beyond available index coverage.")
    required_warmup = max(
        int(warmup_days),
        int(getattr(stg, "stock_universe_min_bars", 0)) + 80,
        int(getattr(stg, "etf_universe_min_bars", 0)) + 40,
        int(getattr(stg, "regime_ma_window", 0)) + int(getattr(stg, "regime_slope_window", 0)) + 20,
        int(getattr(stg, "risk_budget_lookback", 0)) + 40,
    )
    warmup_start_pos = max(0, start_pos - required_warmup)
    run_start = idx_all[warmup_start_pos]

    cs_run = slice_period(close_s_all, run_start, test_end)
    ce_run = slice_period(close_e_all, run_start, test_end)
    vs_run = slice_period(value_s_all, run_start, test_end)
    ve_run = slice_period(value_e_all, run_start, test_end)
    out_full, m_full = run_one(cs_run, ce_run, stg, min_common_dates=min_common_dates, traded_value_s=vs_run, traded_value_e=ve_run, flow_mats=flow_mats, quality_mats=quality_mats)
    out_test = out_full.loc[(out_full.index >= test_start) & (out_full.index <= test_end)]
    m_test = _window_metrics(out_test)
    return m_test, m_full


def run_hybrid_test_with_warmup(
    close_s_all: pd.DataFrame,
    close_e_all: pd.DataFrame,
    value_s_all: pd.DataFrame,
    value_e_all: pd.DataFrame,
    flow_mats: Dict[str, pd.DataFrame] | None,
    quality_mats: Dict[str, pd.DataFrame] | None,
    test_start: pd.Timestamp,
    test_end: pd.Timestamp,
    strategy_name: str,
    named_strategy_map: Dict[str, StrategyConfig],
    min_common_dates: int,
    warmup_days: int = 260,
) -> Tuple[Dict[str, float], Dict[str, float]]:
    spec = HYBRID_STRATEGY_COMPONENTS.get(strategy_name)
    if spec is None:
        raise ValueError(f"Unsupported hybrid strategy: {strategy_name}")

    idx_all = close_s_all.index.intersection(close_e_all.index).sort_values()
    if len(idx_all) < min_common_dates:
        raise RuntimeError("Not enough common dates for hybrid warmup evaluation.")

    start_pos = int(np.searchsorted(idx_all.values, np.datetime64(test_start), side="left"))
    if start_pos >= len(idx_all):
        raise RuntimeError("Test start is beyond available index coverage.")
    required_warmup = int(warmup_days)
    for component_name in spec.keys():
        stg = named_strategy_map[component_name]
        required_warmup = max(
            required_warmup,
            int(getattr(stg, "stock_universe_min_bars", 0)) + 80,
            int(getattr(stg, "etf_universe_min_bars", 0)) + 40,
            int(getattr(stg, "regime_ma_window", 0)) + int(getattr(stg, "regime_slope_window", 0)) + 20,
            int(getattr(stg, "risk_budget_lookback", 0)) + 40,
        )
    warmup_start_pos = max(0, start_pos - required_warmup)
    run_start = idx_all[warmup_start_pos]

    cs_run = slice_period(close_s_all, run_start, test_end)
    ce_run = slice_period(close_e_all, run_start, test_end)
    vs_run = slice_period(value_s_all, run_start, test_end)
    ve_run = slice_period(value_e_all, run_start, test_end)

    component_results: Dict[str, Tuple[pd.DataFrame, Dict[str, float]]] = {}
    for component_name in spec.keys():
        stg = named_strategy_map[component_name]
        out_full, m_full = run_one(
            cs_run,
            ce_run,
            stg,
            min_common_dates=min_common_dates,
            traded_value_s=vs_run,
            traded_value_e=ve_run,
            flow_mats=flow_mats,
            quality_mats=quality_mats,
        )
        out_test = out_full.loc[(out_full.index >= test_start) & (out_full.index <= test_end)].copy()
        component_results[component_name] = (out_test, m_full)

    out_test, m_full = blend_strategy_results(strategy_name, component_results)
    m_test = _window_metrics(out_test)
    return m_test, m_full


def summarize_walkforward(results: pd.DataFrame, benchmark_name: str) -> pd.DataFrame:
    rows: List[Dict[str, float]] = []
    if results.empty:
        return pd.DataFrame()
    bench = results[results["StrategyName"] == benchmark_name][["WindowStart", "CAGR_net"]].rename(columns={"CAGR_net": "BenchCAGRNet"})
    merged = results.merge(bench, on="WindowStart", how="left")

    for s, g in merged.groupby("StrategyName"):
        c = g["CAGR_net"].astype(float)
        m = g["MDD"].astype(float)
        win_rate = float((g["CAGR_net"] > g["BenchCAGRNet"]).mean()) if s != benchmark_name else 1.0
        rows.append(
            {
                "StrategyName": s,
                "WindowCount": int(len(g)),
                "MedianCAGR": float(c.median()),
                "WorstCAGR": float(c.min()),
                "MedianMDD": float(m.median()),
                "WorstMDD": float(m.min()),
                "WinRate_vs_Benchmark": win_rate,
                "CAGRStd": float(c.std(ddof=0)),
            }
        )
    return pd.DataFrame(rows).sort_values(["MedianCAGR", "WorstMDD", "StrategyName"], ascending=[False, False, True]).reset_index(drop=True)


def main() -> None:
    p = argparse.ArgumentParser(description="Run rolling walk-forward validation with automatic feasible-window fallback.")
    p.add_argument("--base", type=str, default=(f"gs://{config.GCS_BUCKET_NAME}/prices" if config.GCS_BUCKET_NAME else "data/prices"))
    p.add_argument("--max-files", type=int, default=0)
    p.add_argument("--flow-base", type=str, default=default_flow_base())
    p.add_argument("--quality-base", type=str, default=default_quality_base())
    p.add_argument("--save-path", type=str, default=(f"gs://{config.GCS_BUCKET_NAME}/backtests/kis_walkforward_results.csv" if config.GCS_BUCKET_NAME else "kis_walkforward_results.csv"))
    p.add_argument("--summary-path", type=str, default=(f"gs://{config.GCS_BUCKET_NAME}/backtests/kis_walkforward_summary.csv" if config.GCS_BUCKET_NAME else "kis_walkforward_summary.csv"))
    p.add_argument("--train-years", type=int, default=8)
    p.add_argument("--test-years", type=int, default=2)
    p.add_argument("--step-years", type=int, default=1)
    p.add_argument("--min-oos-windows", type=int, default=3, help="Target minimum number of OOS windows for stability analysis.")
    p.add_argument("--min-common-dates", type=int, default=180)
    p.add_argument("--rebalance", type=str, default="W-FRI", choices=["W-FRI", "W-2FRI", "D"])
    p.add_argument("--top-n", type=int, default=20)
    p.add_argument("--regime-filter", type=int, default=1)
    p.add_argument("--stop-loss-pct", type=float, default=0.12)
    p.add_argument("--trend-exit-ma", type=int, default=60)
    p.add_argument("--regime-ma-window", type=int, default=200)
    p.add_argument("--regime-slope-window", type=int, default=20)
    p.add_argument("--regime-breadth-threshold", type=float, default=0.55)
    p.add_argument("--vol-lookback", type=int, default=20)
    p.add_argument("--target-vol-annual", type=float, default=0.20)
    p.add_argument("--max-weight", type=float, default=0.20)
    p.add_argument("--min-gross-exposure", type=float, default=0.50)
    p.add_argument("--allow-intraperiod-reentry", type=int, default=1)
    p.add_argument("--reentry-cooldown-days", type=int, default=0)
    p.add_argument("--score-top-k", type=int, default=50)
    p.add_argument("--score-power", type=float, default=1.5)
    p.add_argument("--regime-off-exposure", type=float, default=0.40)
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
    p.add_argument("--range-slope-threshold", type=float, default=0.015)
    p.add_argument("--range-dist-threshold", type=float, default=0.03)
    p.add_argument("--range-breakout-persistence-threshold", type=float, default=0.35)
    p.add_argument("--range-breadth-tolerance", type=float, default=0.15)
    args = p.parse_args()

    print("loading stock close matrix...")
    close_s, value_s = build_market_matrices(args.base, "stock", args.max_files)
    print("loading etf close matrix...")
    close_e, value_e = build_market_matrices(args.base, "etf", args.max_files)
    flow_mats = build_flow_matrices(args.flow_base, market="stock", max_files=args.max_files)
    quality_mats = build_quality_matrices(args.quality_base, close_s.index, list(close_s.columns))
    idx = close_s.index.intersection(close_e.index)
    close_s = close_s.loc[idx]
    close_e = close_e.loc[idx]
    value_s = value_s.loc[idx, close_s.columns]
    value_e = value_e.loc[idx, close_e.columns]
    print(f"stock_tickers={close_s.shape[1]}, etf_tickers={close_e.shape[1]}")

    train_years, test_years, step_years, used_fallback = choose_feasible_window_params(
        idx, args.train_years, args.test_years, args.step_years, max(1, int(args.min_oos_windows))
    )
    common_years = max(float((pd.Timestamp(idx.max()) - pd.Timestamp(idx.min())).days) / 365.25, 0.0) if len(idx) else 0.0
    print(f"common_coverage_years={common_years:.2f}")
    if used_fallback:
        print(
            f"[FALLBACK] requested train/test/step={args.train_years}/{args.test_years}/{args.step_years}y "
            f"-> using feasible {train_years}/{test_years}/{step_years}y"
        )
    windows = build_windows(idx, train_years, test_years, step_years)
    if not windows:
        print("No valid walk-forward windows generated for the provided date range and parameters.")
        empty_cols = [
            "WindowStart",
            "WindowEnd",
            "TrainStart",
            "TrainEnd",
            "TestStart",
            "TestEnd",
            "StrategyName",
            "CAGR",
            "MDD",
            "Sharpe",
            "AnnualTurnover",
            "Trades",
            "CAGR_net",
        ]
        write_csv_any(pd.DataFrame(columns=empty_cols), args.save_path, index=False)
        write_csv_any(
            pd.DataFrame(columns=["StrategyName", "WindowCount", "MedianCAGR", "WorstCAGR", "MedianMDD", "WorstMDD", "WinRate_vs_Benchmark", "CAGRStd"]),
            args.summary_path,
            index=False,
        )
        print(f"saved {args.save_path}")
        print(f"saved {args.summary_path}")
        return

    combos = [Combo(n, pwr, roe) for n, pwr, roe in itertools.product([30, 50, 70], [1.0, 1.5, 2.0], [0.2, 0.4, 0.6])]
    named_strategies_g = build_named_strategies(args, fee_rate=0.0)
    named_strategies_g_map = {stg.name: stg for stg in named_strategies_g}
    named_strategies_n = {stg.name: stg for stg in build_named_strategies(args, fee_rate=0.005 / 2.0)}
    fee_net = 0.005 / 2.0  # roundtrip 0.5%
    bench_name = "Benchmark Weekly Top20"

    rows: List[Dict[str, float]] = []
    for train_start, train_end, test_start, test_end in progress(windows, desc="Walk-forward windows"):
        cs_tr = slice_period(close_s, train_start, train_end)
        ce_tr = slice_period(close_e, train_start, train_end)
        vs_tr = slice_period(value_s, train_start, train_end)
        ve_tr = slice_period(value_e, train_start, train_end)
        cs_te = slice_period(close_s, test_start, test_end)
        ce_te = slice_period(close_e, test_start, test_end)
        if len(cs_tr.index.intersection(ce_tr.index)) < args.min_common_dates:
            continue
        if len(cs_te.index.intersection(ce_te.index)) < max(80, args.min_common_dates // 2):
            continue

        # 1) Select best combo on train by net CAGR.
        best_combo: Combo = combos[0]
        best_train_cagr = -1e18
        for combo in progress(combos, desc=f"Train select {train_start:%Y-%m-%d}", leave=False):
            stg_train = make_score_strategy(args, combo, fee_rate=fee_net)
            _, m_train = run_one(cs_tr, ce_tr, stg_train, min_common_dates=args.min_common_dates, traded_value_s=vs_tr, traded_value_e=ve_tr, quality_mats=quality_mats)
            if float(m_train["CAGR"]) > best_train_cagr:
                best_train_cagr = float(m_train["CAGR"])
                best_combo = combo

        # 2) OOS test for chosen strategy (gross + net).
        stg_test_g = make_score_strategy(args, best_combo, fee_rate=0.0)
        stg_test_n = make_score_strategy(args, best_combo, fee_rate=fee_net)
        m_g, _ = run_test_with_warmup(
                close_s,
                close_e,
                value_s,
                value_e,
                flow_mats,
                quality_mats,
                test_start=test_start,
                test_end=test_end,
                stg=stg_test_g,
            min_common_dates=max(80, args.min_common_dates // 2),
        )
        m_n, m_n_full = run_test_with_warmup(
                close_s,
                close_e,
                value_s,
                value_e,
                flow_mats,
                quality_mats,
                test_start=test_start,
                test_end=test_end,
                stg=stg_test_n,
            min_common_dates=max(80, args.min_common_dates // 2),
        )
        trades_n = int(m_n_full.get("BuyTrades", 0)) + int(m_n_full.get("SellTrades", 0))

        rows.append(
            {
                "WindowStart": train_start.strftime("%Y-%m-%d"),
                "WindowEnd": test_end.strftime("%Y-%m-%d"),
                "TrainStart": train_start.strftime("%Y-%m-%d"),
                "TrainEnd": train_end.strftime("%Y-%m-%d"),
                "TestStart": test_start.strftime("%Y-%m-%d"),
                "TestEnd": test_end.strftime("%Y-%m-%d"),
                "StrategyName": best_combo.name,
                "CAGR": float(m_g["CAGR"]),
                "MDD": float(m_n["MDD"]),
                "Sharpe": float(m_n["Sharpe"]),
                "AnnualTurnover": float(m_n_full.get("AnnualTurnover", 0.0)),
                "Trades": trades_n,
                "CAGR_net": float(m_n["CAGR"]),
            }
        )

        # Direct OOS evaluation for canonical named strategies.
        for stg_g in progress(named_strategies_g, desc=f"Named eval {test_start:%Y-%m-%d}", leave=False):
            stg_n = named_strategies_n[stg_g.name]
            nm_g, _ = run_test_with_warmup(
                close_s,
                close_e,
                value_s,
                  value_e,
                  flow_mats,
                  quality_mats,
                  test_start=test_start,
                test_end=test_end,
                stg=stg_g,
                min_common_dates=max(80, args.min_common_dates // 2),
            )
            nm_n, nm_n_full = run_test_with_warmup(
                close_s,
                close_e,
                value_s,
                  value_e,
                  flow_mats,
                  quality_mats,
                  test_start=test_start,
                test_end=test_end,
                stg=stg_n,
                min_common_dates=max(80, args.min_common_dates // 2),
            )
            trades_named = int(nm_n_full.get("BuyTrades", 0)) + int(nm_n_full.get("SellTrades", 0))
            rows.append(
                {
                    "WindowStart": train_start.strftime("%Y-%m-%d"),
                    "WindowEnd": test_end.strftime("%Y-%m-%d"),
                    "TrainStart": train_start.strftime("%Y-%m-%d"),
                    "TrainEnd": train_end.strftime("%Y-%m-%d"),
                    "TestStart": test_start.strftime("%Y-%m-%d"),
                    "TestEnd": test_end.strftime("%Y-%m-%d"),
                    "StrategyName": stg_g.name,
                    "CAGR": float(nm_g["CAGR"]),
                    "MDD": float(nm_n["MDD"]),
                    "Sharpe": float(nm_n["Sharpe"]),
                    "AnnualTurnover": float(nm_n_full.get("AnnualTurnover", 0.0)),
                    "Trades": trades_named,
                    "CAGR_net": float(nm_n["CAGR"]),
                }
            )

        for hybrid_name in HYBRID_STRATEGY_COMPONENTS.keys():
            hm_g, _ = run_hybrid_test_with_warmup(
                close_s,
                close_e,
                value_s,
                value_e,
                flow_mats,
                test_start=test_start,
                test_end=test_end,
                strategy_name=hybrid_name,
                named_strategy_map=named_strategies_g_map,
                min_common_dates=max(80, args.min_common_dates // 2),
            )
            hm_n, hm_n_full = run_hybrid_test_with_warmup(
                close_s,
                close_e,
                value_s,
                value_e,
                flow_mats,
                test_start=test_start,
                test_end=test_end,
                strategy_name=hybrid_name,
                named_strategy_map=named_strategies_n,
                min_common_dates=max(80, args.min_common_dates // 2),
            )
            trades_hybrid = int(hm_n_full.get("BuyTrades", 0)) + int(hm_n_full.get("SellTrades", 0))
            rows.append(
                {
                    "WindowStart": train_start.strftime("%Y-%m-%d"),
                    "WindowEnd": test_end.strftime("%Y-%m-%d"),
                    "TrainStart": train_start.strftime("%Y-%m-%d"),
                    "TrainEnd": train_end.strftime("%Y-%m-%d"),
                    "TestStart": test_start.strftime("%Y-%m-%d"),
                    "TestEnd": test_end.strftime("%Y-%m-%d"),
                    "StrategyName": hybrid_name,
                    "CAGR": float(hm_g["CAGR"]),
                    "MDD": float(hm_n["MDD"]),
                    "Sharpe": float(hm_n["Sharpe"]),
                    "AnnualTurnover": float(hm_n_full.get("AnnualTurnover", 0.0)),
                    "Trades": trades_hybrid,
                    "CAGR_net": float(hm_n["CAGR"]),
                }
            )

        # Benchmark row on same test window.
        b_g = make_benchmark(args, fee_rate=0.0)
        b_n = make_benchmark(args, fee_rate=fee_net)
        bm_g, _ = run_test_with_warmup(
            close_s,
            close_e,
            value_s,
            value_e,
            flow_mats,
            test_start=test_start,
            test_end=test_end,
            stg=b_g,
            min_common_dates=max(80, args.min_common_dates // 2),
        )
        bm_n, bm_n_full = run_test_with_warmup(
            close_s,
            close_e,
            value_s,
            value_e,
            flow_mats,
            test_start=test_start,
            test_end=test_end,
            stg=b_n,
            min_common_dates=max(80, args.min_common_dates // 2),
        )
        trades_b = int(bm_n_full.get("BuyTrades", 0)) + int(bm_n_full.get("SellTrades", 0))
        rows.append(
            {
                "WindowStart": train_start.strftime("%Y-%m-%d"),
                "WindowEnd": test_end.strftime("%Y-%m-%d"),
                "TrainStart": train_start.strftime("%Y-%m-%d"),
                "TrainEnd": train_end.strftime("%Y-%m-%d"),
                "TestStart": test_start.strftime("%Y-%m-%d"),
                "TestEnd": test_end.strftime("%Y-%m-%d"),
                "StrategyName": bench_name,
                "CAGR": float(bm_g["CAGR"]),
                "MDD": float(bm_n["MDD"]),
                "Sharpe": float(bm_n["Sharpe"]),
                "AnnualTurnover": float(bm_n_full.get("AnnualTurnover", 0.0)),
                "Trades": trades_b,
                "CAGR_net": float(bm_n["CAGR"]),
            }
        )

    if not rows:
        print("No walk-forward rows survived train/test minimum-date filters; writing empty outputs.")
        empty_cols = [
            "WindowStart",
            "WindowEnd",
            "TrainStart",
            "TrainEnd",
            "TestStart",
            "TestEnd",
            "StrategyName",
            "CAGR",
            "MDD",
            "Sharpe",
            "AnnualTurnover",
            "Trades",
            "CAGR_net",
        ]
        write_csv_any(pd.DataFrame(columns=empty_cols), args.save_path, index=False)
        write_csv_any(
            pd.DataFrame(columns=["StrategyName", "WindowCount", "MedianCAGR", "WorstCAGR", "MedianMDD", "WorstMDD", "WinRate_vs_Benchmark", "CAGRStd"]),
            args.summary_path,
            index=False,
        )
        print(f"saved {args.save_path}")
        print(f"saved {args.summary_path}")
        return

    out = pd.DataFrame(rows).sort_values(["WindowStart", "TestStart", "StrategyName"]).reset_index(drop=True)
    write_csv_any(out, args.save_path, index=False)
    print(f"saved {args.save_path}")
    print(f"walkforward_rows={len(out)}, windows={len(windows)}")
    print("\n=== Walk-forward results (top 12 rows) ===")
    print(out.head(12).to_string(index=False))

    summary = summarize_walkforward(out, benchmark_name=bench_name)
    write_csv_any(summary, args.summary_path, index=False)
    print(f"saved {args.summary_path}")
    print("\n=== Walk-forward summary ===")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
