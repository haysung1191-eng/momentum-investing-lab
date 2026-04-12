import argparse
import sys
from typing import Dict, List

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


def parse_roundtrip_costs(text: str) -> List[float]:
    out: List[float] = []
    for part in text.split(","):
        s = part.strip()
        if not s:
            continue
        out.append(round(float(s), 4))
    return sorted(set(out))


def build_strategies(args: argparse.Namespace, fee_rate: float) -> List[StrategyConfig]:
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


def main() -> None:
    p = argparse.ArgumentParser(description="Run extended roundtrip-cost sensitivity table for core strategies.")
    p.add_argument("--base", type=str, default=(f"gs://{config.GCS_BUCKET_NAME}/prices" if config.GCS_BUCKET_NAME else "data/prices"))
    p.add_argument("--flow-base", type=str, default=default_flow_base())
    p.add_argument("--quality-base", type=str, default=default_quality_base())
    p.add_argument("--top-n", type=int, default=20)
    p.add_argument("--max-files", type=int, default=0, help="0 means all")
    p.add_argument("--min-common-dates", type=int, default=180)
    p.add_argument("--save-path", type=str, default=(f"gs://{config.GCS_BUCKET_NAME}/backtests/kis_bt_cost_sensitivity_extended.csv" if config.GCS_BUCKET_NAME else "kis_bt_cost_sensitivity_extended.csv"))
    p.add_argument("--roundtrip-costs", type=str, default="0.20,0.35,0.50,0.60,0.80,1.00", help="Percent list, e.g. 0.20,0.35,0.50")
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
    p.add_argument("--score-top-k", type=int, default=50)
    p.add_argument("--score-power", type=float, default=1.5)
    p.add_argument("--regime-off-exposure", type=float, default=0.40)
    p.add_argument("--allow-intraperiod-reentry", type=int, default=1)
    p.add_argument("--reentry-cooldown-days", type=int, default=0)
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

    roundtrip_costs = parse_roundtrip_costs(args.roundtrip_costs)
    if not roundtrip_costs:
        raise ValueError("No valid roundtrip costs provided.")

    print("loading stock close matrix...")
    close_s, value_s = build_market_matrices(args.base, "stock", args.max_files)
    print("loading etf close matrix...")
    close_e, value_e = build_market_matrices(args.base, "etf", args.max_files)
    flow_mats = build_flow_matrices(args.flow_base, market="stock", max_files=args.max_files)
    quality_mats = build_quality_matrices(args.quality_base, close_s.index, list(close_s.columns))
    print(f"stock_tickers={close_s.shape[1]}, etf_tickers={close_e.shape[1]}")

    # Gross baseline (fee=0) for cost drag reference.
    gross_strategies = build_strategies(args, fee_rate=0.0)
    gross_map: Dict[str, Dict[str, float]] = {}
    gross_components: Dict[str, tuple[pd.DataFrame, Dict[str, float]]] = {}
    for stg in progress(gross_strategies, desc="Gross baseline", dynamic_ncols=True, file=sys.stdout):
        out, m = run_one(close_s, close_e, stg, min_common_dates=args.min_common_dates, traded_value_s=value_s, traded_value_e=value_e, flow_mats=flow_mats, quality_mats=quality_mats)
        gross_map[stg.name] = m
        gross_components[stg.name] = (out, m)
    for hybrid_name in HYBRID_STRATEGY_COMPONENTS.keys():
        if all(component_name in gross_components for component_name in HYBRID_STRATEGY_COMPONENTS[hybrid_name].keys()):
            _, m = blend_strategy_results(hybrid_name, gross_components)
            gross_map[hybrid_name] = m

    rows: List[Dict[str, float]] = []
    for rt_pct in progress(roundtrip_costs, desc="Cost scenarios", dynamic_ncols=True, file=sys.stdout):
        # Turnover in this engine is buy+sell notional, so apply one-way fee to turnover.
        fee_oneway = (rt_pct / 100.0) / 2.0
        print(f"running roundtrip_cost={rt_pct:.2f}% (oneway={fee_oneway:.4%}) ...")
        strategies = build_strategies(args, fee_rate=fee_oneway)
        cost_components: Dict[str, tuple[pd.DataFrame, Dict[str, float]]] = {}
        for stg in progress(strategies, desc=f"Strategies@{rt_pct:.2f}%", leave=False, dynamic_ncols=True, file=sys.stdout):
            out, m = run_one(close_s, close_e, stg, min_common_dates=args.min_common_dates, traded_value_s=value_s, traded_value_e=value_e, flow_mats=flow_mats, quality_mats=quality_mats)
            cost_components[stg.name] = (out, m)
            gross = gross_map[stg.name]
            trades = int(m.get("BuyTrades", 0)) + int(m.get("SellTrades", 0))
            row = {
                "StrategyName": stg.name,
                "RoundtripCostPct": rt_pct,
                "CAGR_gross": float(gross["CAGR"]),
                "CAGR_net": float(m["CAGR"]),
                "CAGR_drag": float(gross["CAGR"] - m["CAGR"]),
                "AnnualTurnover": float(m.get("AnnualTurnover", 0.0)),
                "Trades": trades,
                # Extra diagnostics
                "MDD_net": float(m["MDD"]),
                "Sharpe_net": float(m["Sharpe"]),
                "FinalNAV_net": float(m["FinalNAV"]),
                "AvgTurnover": float(m.get("AvgTurnover", 0.0)),
                "AvgHoldings": float(m.get("AvgHoldings", 0.0)),
                "RebalanceCount": int(m.get("RebalanceCount", 0)),
            }
            rows.append(row)
        for hybrid_name in HYBRID_STRATEGY_COMPONENTS.keys():
            if not all(component_name in cost_components for component_name in HYBRID_STRATEGY_COMPONENTS[hybrid_name].keys()):
                continue
            _, m = blend_strategy_results(hybrid_name, cost_components)
            gross = gross_map[hybrid_name]
            trades = int(m.get("BuyTrades", 0)) + int(m.get("SellTrades", 0))
            rows.append(
                {
                    "StrategyName": hybrid_name,
                    "RoundtripCostPct": rt_pct,
                    "CAGR_gross": float(gross["CAGR"]),
                    "CAGR_net": float(m["CAGR"]),
                    "CAGR_drag": float(gross["CAGR"] - m["CAGR"]),
                    "AnnualTurnover": float(m.get("AnnualTurnover", 0.0)),
                    "Trades": trades,
                    "MDD_net": float(m["MDD"]),
                    "Sharpe_net": float(m["Sharpe"]),
                    "FinalNAV_net": float(m["FinalNAV"]),
                    "AvgTurnover": float(m.get("AvgTurnover", 0.0)),
                    "AvgHoldings": float(m.get("AvgHoldings", 0.0)),
                    "RebalanceCount": int(m.get("RebalanceCount", 0)),
                }
            )

    out = pd.DataFrame(rows).sort_values(["RoundtripCostPct", "CAGR_net", "StrategyName"], ascending=[True, False, True]).reset_index(drop=True)
    write_csv_any(out, args.save_path, index=False)
    print(f"saved {args.save_path}")
    print("\n=== Cost sensitivity (top 12 rows) ===")
    print(out.head(12).to_string(index=False))

    # Print compact pivot for quick inspection.
    piv = out.pivot_table(index="StrategyName", columns="RoundtripCostPct", values="CAGR_net", aggfunc="first")
    print("\n=== CAGR_net by Roundtrip Cost ===")
    print(piv.to_string())


if __name__ == "__main__":
    main()
