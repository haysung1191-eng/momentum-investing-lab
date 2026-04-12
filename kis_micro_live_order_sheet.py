import argparse
from pathlib import Path

import pandas as pd


def build_initial_sheet(portfolio: pd.DataFrame, capital: float, trade_date: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for _, r in portfolio.iterrows():
        px = float(r["CurrentPrice"])
        target_weight = float(r["TargetWeight"])
        target = capital * target_weight
        shares = int(target // px) if px > 0 else 0
        notional = shares * px
        rows.append(
            {
                "TradeDate": trade_date,
                "AsOfDate": r["AsOfDate"],
                "Strategy": r["Strategy"],
                "Code": r["Code"],
                "AssetType": r.get("AssetType", ""),
                "TargetWeight": target_weight,
                "CurrentPrice": px,
                "TargetNotionalKRW": round(target, 2),
                "OrderShares": shares,
                "OrderNotionalKRW": round(notional, 2),
                "Action": "BUY",
                "OrderMode": "INITIAL",
            }
        )
    order_df = pd.DataFrame(rows)
    summary = pd.DataFrame(
        [
            {
                "TradeDate": trade_date,
                "AsOfDate": str(portfolio["AsOfDate"].iloc[0]) if not portfolio.empty else "",
                "Strategy": str(portfolio["Strategy"].iloc[0]) if not portfolio.empty else "",
                "OrderMode": "INITIAL",
                "PlannedCapitalKRW": capital,
                "PlannedInvestedKRW": float(order_df["OrderNotionalKRW"].sum()) if not order_df.empty else 0.0,
                "ResidualCashKRW": float(capital - order_df["OrderNotionalKRW"].sum()) if not order_df.empty else capital,
                "HoldingsCount": int((order_df["OrderShares"] > 0).sum()) if not order_df.empty else 0,
            }
        ]
    )
    return order_df, summary


def build_rebalance_sheet(diff_df: pd.DataFrame, strategy: str, capital: float, trade_date: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    diff_df = diff_df[diff_df["Strategy"].astype(str) == strategy].copy()
    diff_df = diff_df[diff_df["Action"].astype(str) != "HOLD"].copy()
    for _, r in diff_df.iterrows():
        px = float(r["EstimatedPrice"])
        delta_weight = float(abs(r["WeightChange"]))
        target = capital * delta_weight
        shares = int(target // px) if px > 0 else 0
        if shares <= 0 and delta_weight > 0:
            continue
        raw_action = str(r["Action"])
        action = "BUY" if raw_action in {"BUY", "INCREASE"} else "SELL"
        rows.append(
            {
                "TradeDate": trade_date,
                "AsOfDate": r["AsOfDate"],
                "Strategy": strategy,
                "Code": r["Code"],
                "PrevWeight": float(r["PrevWeight"]),
                "NewWeight": float(r["NewWeight"]),
                "WeightChange": float(r["WeightChange"]),
                "CurrentPrice": px,
                "TargetNotionalKRW": round(target, 2),
                "OrderShares": shares,
                "OrderNotionalKRW": round(shares * px, 2),
                "Action": action,
                "OrderMode": "REBALANCE",
            }
        )
    order_df = pd.DataFrame(rows)
    summary = pd.DataFrame(
        [
            {
                "TradeDate": trade_date,
                "AsOfDate": str(diff_df["AsOfDate"].iloc[0]) if not diff_df.empty else "",
                "Strategy": strategy,
                "OrderMode": "REBALANCE",
                "PlannedCapitalKRW": capital,
                "PlannedBuyKRW": float(order_df.loc[order_df["Action"].eq("BUY"), "OrderNotionalKRW"].sum()) if not order_df.empty else 0.0,
                "PlannedSellKRW": float(order_df.loc[order_df["Action"].eq("SELL"), "OrderNotionalKRW"].sum()) if not order_df.empty else 0.0,
                "TradeCount": int(len(order_df)),
            }
        ]
    )
    return order_df, summary


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build Korea micro-live order sheet for initial or rebalance execution.")
    p.add_argument("--portfolio-path", type=str, default="backtests/kis_shadow_portfolio.csv")
    p.add_argument("--diff-path", type=str, default="backtests/kis_shadow_rebalance_diff.csv")
    p.add_argument("--strategy-name", type=str, default="Weekly ETF RiskBudget")
    p.add_argument("--capital-krw", type=float, default=3000000.0)
    p.add_argument("--trade-date", type=str, default="2026-03-30")
    p.add_argument("--mode", type=str, choices=["initial", "rebalance"], default="initial")
    p.add_argument("--save-path", type=str, default="")
    p.add_argument("--summary-path", type=str, default="")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    portfolio = pd.read_csv(args.portfolio_path)
    diff_df = pd.read_csv(args.diff_path)
    strategy = args.strategy_name
    portfolio = portfolio[portfolio["Strategy"].astype(str) == strategy].copy()

    if args.mode == "initial":
        order_df, summary_df = build_initial_sheet(portfolio, args.capital_krw, args.trade_date)
        save_path = args.save_path or f"backtests/etf_riskbudget_micro_live_initial_sheet_{int(args.capital_krw)}krw.csv"
        summary_path = args.summary_path or f"backtests/etf_riskbudget_micro_live_initial_sheet_{int(args.capital_krw)}krw_summary.csv"
    else:
        order_df, summary_df = build_rebalance_sheet(diff_df, strategy, args.capital_krw, args.trade_date)
        save_path = args.save_path or f"backtests/etf_riskbudget_micro_live_rebalance_sheet_{int(args.capital_krw)}krw.csv"
        summary_path = args.summary_path or f"backtests/etf_riskbudget_micro_live_rebalance_sheet_{int(args.capital_krw)}krw_summary.csv"

    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    order_df.to_csv(save_path, index=False)
    summary_df.to_csv(summary_path, index=False)
    print(order_df.to_string(index=False) if not order_df.empty else "EMPTY")
    print()
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
