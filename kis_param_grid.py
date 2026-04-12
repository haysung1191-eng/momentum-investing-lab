import argparse
import itertools
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple

import pandas as pd

import config
from kis_backtest_from_prices import StrategyConfig, build_market_matrices, run_one, write_csv_any

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


def config_name(n: int, power: float, roe: float) -> str:
    return f"ScoreN{n}_P{power:.1f}_ROE{roe:.1f}"


def make_score_strategy(args: argparse.Namespace, n: int, power: float, roe: float, fee_rate: float) -> StrategyConfig:
    k_per_sleeve = max(1, int(n) // 2)
    return StrategyConfig(
        name=config_name(n, power, roe),
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
        score_power=power,
        regime_off_exposure=roe,
        allow_intraperiod_reentry=bool(args.allow_intraperiod_reentry),
        reentry_cooldown_days=args.reentry_cooldown_days,
    )


_W_CLOSE_S: Optional[pd.DataFrame] = None
_W_CLOSE_E: Optional[pd.DataFrame] = None
_W_VALUE_S: Optional[pd.DataFrame] = None
_W_VALUE_E: Optional[pd.DataFrame] = None
_W_ARGS: Optional[argparse.Namespace] = None


def _worker_init(args_dict: Dict) -> None:
    global _W_CLOSE_S, _W_CLOSE_E, _W_VALUE_S, _W_VALUE_E, _W_ARGS
    ns = argparse.Namespace(**args_dict)
    _W_ARGS = ns
    _W_CLOSE_S, _W_VALUE_S = build_market_matrices(ns.base, "stock", ns.max_files)
    _W_CLOSE_E, _W_VALUE_E = build_market_matrices(ns.base, "etf", ns.max_files)


def _eval_one(combo: Tuple[int, float, float]) -> Dict[str, float]:
    global _W_CLOSE_S, _W_CLOSE_E, _W_VALUE_S, _W_VALUE_E, _W_ARGS
    if _W_CLOSE_S is None or _W_CLOSE_E is None or _W_VALUE_S is None or _W_VALUE_E is None or _W_ARGS is None:
        raise RuntimeError("Worker not initialized.")
    n, power, roe = combo
    gross_stg = make_score_strategy(_W_ARGS, n=n, power=power, roe=roe, fee_rate=0.0)
    net_stg = make_score_strategy(_W_ARGS, n=n, power=power, roe=roe, fee_rate=0.005 / 2.0)
    _, m_gross = run_one(_W_CLOSE_S, _W_CLOSE_E, gross_stg, min_common_dates=_W_ARGS.min_common_dates, traded_value_s=_W_VALUE_S, traded_value_e=_W_VALUE_E)
    _, m_net = run_one(_W_CLOSE_S, _W_CLOSE_E, net_stg, min_common_dates=_W_ARGS.min_common_dates, traded_value_s=_W_VALUE_S, traded_value_e=_W_VALUE_E)
    trades = int(m_net.get("BuyTrades", 0)) + int(m_net.get("SellTrades", 0))
    return {
        "StrategyConfig": gross_stg.name,
        "N": int(n),
        "score_power": float(power),
        "regime_off_exposure": float(roe),
        "CAGR": float(m_gross["CAGR"]),
        "MDD": float(m_gross["MDD"]),
        "Sharpe": float(m_gross["Sharpe"]),
        "AnnualTurnover": float(m_gross.get("AnnualTurnover", 0.0)),
        "Trades": trades,
        "CAGR_net_0.5pct_cost": float(m_net["CAGR"]),
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Evaluate 27 score-strategy parameter combos with gross/net metrics.")
    p.add_argument("--base", type=str, default=(f"gs://{config.GCS_BUCKET_NAME}/prices" if config.GCS_BUCKET_NAME else "data/prices"))
    p.add_argument("--max-files", type=int, default=0)
    p.add_argument("--min-common-dates", type=int, default=180)
    p.add_argument("--top-n", type=int, default=20)
    p.add_argument("--rebalance", type=str, default="W-FRI", choices=["W-FRI", "W-2FRI", "D"])
    p.add_argument("--save-path", type=str, default=(f"gs://{config.GCS_BUCKET_NAME}/backtests/kis_param_grid_results.csv" if config.GCS_BUCKET_NAME else "kis_param_grid_results.csv"))
    p.add_argument("--workers", type=int, default=1)
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
    args = p.parse_args()

    n_grid = [30, 50, 70]
    power_grid = [1.0, 1.5, 2.0]
    roe_grid = [0.2, 0.4, 0.6]
    combos: List[Tuple[int, float, float]] = list(itertools.product(n_grid, power_grid, roe_grid))

    rows: List[Dict[str, float]] = []
    if args.workers > 1:
        args_dict = vars(args).copy()
        with ProcessPoolExecutor(max_workers=args.workers, initializer=_worker_init, initargs=(args_dict,)) as ex:
            futs = [ex.submit(_eval_one, c) for c in combos]
            for fut in progress(as_completed(futs), total=len(futs), desc="Grid eval (mp)"):
                rows.append(fut.result())
    else:
        # Single-process execution (deterministic and memory-safe).
        _worker_init(vars(args).copy())
        for c in progress(combos, desc="Grid eval"):
            rows.append(_eval_one(c))

    out = pd.DataFrame(rows)
    if out.empty:
        raise RuntimeError("Parameter grid produced no rows. Check data coverage and min-common-dates.")
    out = out.sort_values(
        ["CAGR_net_0.5pct_cost", "CAGR", "MDD", "N", "score_power", "regime_off_exposure"],
        ascending=[False, False, False, True, True, True],
    ).reset_index(drop=True)
    write_csv_any(out, args.save_path, index=False)
    print(f"saved {args.save_path}")
    print(f"grid_rows={len(out)} (expected=27)")
    print("\n=== Top 10 (CAGR_net_0.5pct_cost) ===")
    print(out.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
