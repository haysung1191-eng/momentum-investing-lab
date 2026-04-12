import argparse
import itertools
from typing import Dict, List, Tuple

import pandas as pd

import config
from kis_backtest_from_prices import StrategyConfig, build_market_matrices, run_one, write_csv_any


def split_train_test(idx: pd.DatetimeIndex, train_ratio: float) -> Tuple[pd.DatetimeIndex, pd.DatetimeIndex]:
    if len(idx) < 20:
        return idx, idx
    cut = max(10, int(len(idx) * train_ratio))
    cut = min(cut, len(idx) - 5)
    return idx[:cut], idx[cut:]


def tail_years(df: pd.DataFrame, years: int) -> pd.DataFrame:
    if df.empty:
        return df
    end = df.index.max()
    start = end - pd.DateOffset(years=years)
    return df.loc[df.index >= start]


def score_row(cagr: float, mdd: float, sharpe: float) -> float:
    drawdown_penalty = abs(min(0.0, mdd))
    return (0.55 * cagr) + (0.45 * sharpe) - (0.80 * drawdown_penalty)


def build_strategies(top_n: int, fee: float, p: Dict[str, float]) -> List[StrategyConfig]:
    common = dict(
        top_n_stock=top_n,
        top_n_etf=top_n,
        fee_rate=fee,
        use_regime_filter=True,
        stop_loss_pct=float(p["stop_loss_pct"]),
        trend_exit_ma=int(p["trend_exit_ma"]),
        regime_ma_window=200,
        regime_slope_window=20,
        regime_breadth_threshold=float(p["regime_breadth_threshold"]),
        vol_lookback=20,
        target_vol_annual=float(p["target_vol_annual"]),
        max_weight=float(p["max_weight"]),
        min_gross_exposure=0.50,
        entry_rank=20,
        exit_rank=25,
    )
    return [
        StrategyConfig(name="Daily Top20", rebalance="D", use_buffer=False, **common),
        StrategyConfig(name="Weekly Top20", rebalance="W-FRI", use_buffer=False, **common),
        StrategyConfig(name="Weekly Buffer 20/25", rebalance="W-FRI", use_buffer=True, **common),
    ]


def run_period(
    close_s: pd.DataFrame,
    close_e: pd.DataFrame,
    value_s: pd.DataFrame,
    value_e: pd.DataFrame,
    years: int,
    top_n: int,
    fee: float,
    min_common_dates: int,
    train_ratio: float,
    param_grid: List[Dict[str, float]],
) -> pd.DataFrame:
    cs = tail_years(close_s, years)
    ce = tail_years(close_e, years)
    vs = tail_years(value_s, years)
    ve = tail_years(value_e, years)
    common_idx = cs.index.intersection(ce.index)
    cs = cs.loc[common_idx]
    ce = ce.loc[common_idx]
    vs = vs.loc[common_idx, cs.columns]
    ve = ve.loc[common_idx, ce.columns]
    train_idx, test_idx = split_train_test(common_idx, train_ratio)

    rows: List[Dict[str, float]] = []
    for p in param_grid:
        stgs = build_strategies(top_n=top_n, fee=fee, p=p)
        tr_scores = []
        te_scores = []
        tr_cagrs = []
        te_cagrs = []
        tr_mdds = []
        te_mdds = []

        for stg in stgs:
            try:
                tr_nav, tr_m = run_one(cs.loc[train_idx], ce.loc[train_idx], stg, min_common_dates=min_common_dates, traded_value_s=vs.loc[train_idx], traded_value_e=ve.loc[train_idx])
                te_nav, te_m = run_one(cs.loc[test_idx], ce.loc[test_idx], stg, min_common_dates=max(60, min_common_dates // 2), traded_value_s=vs.loc[test_idx], traded_value_e=ve.loc[test_idx])
                _ = tr_nav, te_nav
            except Exception:
                tr_m = {"CAGR": -1.0, "MDD": -1.0, "Sharpe": -5.0}
                te_m = {"CAGR": -1.0, "MDD": -1.0, "Sharpe": -5.0}

            tr_scores.append(score_row(tr_m["CAGR"], tr_m["MDD"], tr_m["Sharpe"]))
            te_scores.append(score_row(te_m["CAGR"], te_m["MDD"], te_m["Sharpe"]))
            tr_cagrs.append(float(tr_m["CAGR"]))
            te_cagrs.append(float(te_m["CAGR"]))
            tr_mdds.append(float(tr_m["MDD"]))
            te_mdds.append(float(te_m["MDD"]))

        row: Dict[str, float] = {}
        row.update(p)
        row["period_years"] = years
        row["train_score"] = sum(tr_scores) / len(tr_scores)
        row["test_score"] = sum(te_scores) / len(te_scores)
        row["overall_score"] = (0.4 * row["train_score"]) + (0.6 * row["test_score"])
        row["train_cagr"] = sum(tr_cagrs) / len(tr_cagrs)
        row["test_cagr"] = sum(te_cagrs) / len(te_cagrs)
        row["train_mdd"] = sum(tr_mdds) / len(tr_mdds)
        row["test_mdd"] = sum(te_mdds) / len(te_mdds)
        rows.append(row)

    out = pd.DataFrame(rows)
    out = out.sort_values(["overall_score", "test_score"], ascending=[False, False]).reset_index(drop=True)
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="Grid optimization for KIS momentum+MAD backtest params.")
    p.add_argument("--base", type=str, default=(f"gs://{config.GCS_BUCKET_NAME}/prices" if config.GCS_BUCKET_NAME else "data/prices"))
    p.add_argument("--max-files", type=int, default=0)
    p.add_argument("--top-n", type=int, default=20)
    p.add_argument("--fee-bps", type=float, default=8.0)
    p.add_argument("--min-common-dates", type=int, default=180)
    p.add_argument("--train-ratio", type=float, default=0.7)
    p.add_argument("--period-years", nargs="+", type=int, default=[3, 5])
    p.add_argument("--save-prefix", type=str, default="kis_param_opt")
    args = p.parse_args()

    print("loading stock close matrix...")
    close_s, value_s = build_market_matrices(args.base, "stock", args.max_files)
    print("loading etf close matrix...")
    close_e, value_e = build_market_matrices(args.base, "etf", args.max_files)
    print(f"stock_tickers={close_s.shape[1]}, etf_tickers={close_e.shape[1]}")

    fee = args.fee_bps / 10000.0
    grid = {
        "regime_breadth_threshold": [0.50, 0.55],
        "target_vol_annual": [0.20, 0.24],
        "max_weight": [0.15, 0.20],
        "stop_loss_pct": [0.10, 0.12],
        "trend_exit_ma": [40, 60],
    }
    keys = list(grid.keys())
    values = [grid[k] for k in keys]
    param_grid = [dict(zip(keys, v)) for v in itertools.product(*values)]
    print(f"grid_size={len(param_grid)}")

    period_results: List[pd.DataFrame] = []
    for years in args.period_years:
        print(f"running optimization period={years}y ...")
        df = run_period(
            close_s=close_s,
            close_e=close_e,
            value_s=value_s,
            value_e=value_e,
            years=years,
            top_n=args.top_n,
            fee=fee,
            min_common_dates=args.min_common_dates,
            train_ratio=args.train_ratio,
            param_grid=param_grid,
        )
        period_results.append(df)

    all_df = pd.concat(period_results, ignore_index=True)
    all_df["rank_in_period"] = all_df.groupby("period_years")["overall_score"].rank(ascending=False, method="dense")

    # Consensus winner: best average normalized rank across periods.
    ranked = all_df.copy()
    ranked["norm_rank"] = ranked.groupby("period_years")["rank_in_period"].transform(lambda s: (s - 1) / max(1, (s.max() - 1)))
    key_cols = keys
    consensus = (
        ranked.groupby(key_cols, dropna=False)["norm_rank"]
        .mean()
        .reset_index()
        .sort_values("norm_rank", ascending=True)
        .reset_index(drop=True)
    )
    best = consensus.iloc[0].to_dict()

    print("\n=== Best Consensus Params ===")
    for k in keys:
        print(f"{k}={best[k]}")

    result_path = f"{args.save_prefix}_grid.csv"
    consensus_path = f"{args.save_prefix}_consensus.csv"
    write_csv_any(all_df, result_path, index=False)
    write_csv_any(consensus, consensus_path, index=False)
    print(f"saved {result_path}")
    print(f"saved {consensus_path}")


if __name__ == "__main__":
    main()
