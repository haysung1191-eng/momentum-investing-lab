import argparse

import numpy as np
import pandas as pd

import config
from kis_backtest_from_prices import write_csv_any
from kis_shadow_common import (
    compute_target_portfolio,
    default_backtests_base,
    read_csv_any,
    read_json_any,
    resolve_strategy_name,
)


def pick_fill_price(current_price: float) -> float:
    return float(current_price) if pd.notna(current_price) and current_price > 0 else np.nan


def main() -> None:
    default_base = default_backtests_base()
    p = argparse.ArgumentParser(description="Maintain a simple paper-trading ledger and NAV-like shadow history.")
    p.add_argument("--base", type=str, default=(f"gs://{config.GCS_BUCKET_NAME}/prices" if config.GCS_BUCKET_NAME else "data/prices"))
    p.add_argument("--live-readiness-path", type=str, default=f"{default_base}/kis_live_readiness.csv")
    p.add_argument("--manifest-path", type=str, default=f"{default_base}/kis_pipeline_run_manifest.json")
    p.add_argument("--current-portfolio-path", type=str, default="")
    p.add_argument("--previous-portfolio-path", type=str, default=f"{default_base}/kis_shadow_portfolio.csv")
    p.add_argument("--diff-path", type=str, default=f"{default_base}/kis_shadow_rebalance_diff.csv")
    p.add_argument("--ledger-path", type=str, default=f"{default_base}/kis_shadow_ledger.csv")
    p.add_argument("--nav-path", type=str, default=f"{default_base}/kis_shadow_nav.csv")
    p.add_argument("--strategy-name", type=str, default="")
    p.add_argument("--as-of-date", type=str, default="")
    p.add_argument("--min-common-dates", type=int, default=180)
    p.add_argument("--max-files", type=int, default=0)
    p.add_argument("--starting-capital", type=float, default=10_000_000.0)
    p.add_argument("--one-way-fee-bps", type=float, default=10.0)
    p.add_argument("--one-way-slippage-bps", type=float, default=15.0)
    args = p.parse_args()

    manifest = read_json_any(args.manifest_path)
    strategy_name = resolve_strategy_name(args.live_readiness_path, args.strategy_name or None)
    current_portfolio = read_csv_any(args.current_portfolio_path) if args.current_portfolio_path else pd.DataFrame()
    if not current_portfolio.empty and "Strategy" in current_portfolio.columns:
        current_portfolio = current_portfolio[current_portfolio["Strategy"].astype(str) == strategy_name].copy()
    if current_portfolio.empty:
        current_portfolio, meta = compute_target_portfolio(
            base=args.base,
            strategy_name=strategy_name,
            min_common_dates=args.min_common_dates,
            as_of_date=args.as_of_date or None,
            max_files=args.max_files,
        )
    else:
        meta = {
            "AsOfDate": str(current_portfolio["AsOfDate"].iloc[0]) if "AsOfDate" in current_portfolio.columns and not current_portfolio.empty else "",
        }
    diff_df = read_csv_any(args.diff_path)
    if not diff_df.empty and "Strategy" in diff_df.columns:
        diff_df = diff_df[diff_df["Strategy"].astype(str) == strategy_name].copy()
    prev_portfolio = read_csv_any(args.previous_portfolio_path) if args.previous_portfolio_path else pd.DataFrame()
    if not prev_portfolio.empty and "Strategy" in prev_portfolio.columns:
        prev_portfolio = prev_portfolio[prev_portfolio["Strategy"].astype(str) == strategy_name].copy()
    prev_nav = read_csv_any(args.nav_path)
    if not prev_nav.empty and "Strategy" in prev_nav.columns:
        prev_nav = prev_nav[prev_nav["Strategy"].astype(str) == strategy_name].copy()
    prev_ledger = read_csv_any(args.ledger_path)
    if not prev_ledger.empty and "Strategy" in prev_ledger.columns:
        prev_ledger = prev_ledger[prev_ledger["Strategy"].astype(str) == strategy_name].copy()

    fee_rate = args.one_way_fee_bps / 10000.0
    slippage_rate = args.one_way_slippage_bps / 10000.0

    last_nav = float(prev_nav.iloc[-1]["ShadowNAV"]) if not prev_nav.empty else float(args.starting_capital)
    last_cash = float(prev_nav.iloc[-1]["Cash"]) if not prev_nav.empty else float(args.starting_capital)

    prev_weights = {str(r["Code"]): float(r.get("TargetWeight", 0.0)) for _, r in prev_portfolio.iterrows()} if not prev_portfolio.empty else {}
    prev_prices = {str(r["Code"]): float(r.get("CurrentPrice", np.nan)) for _, r in prev_portfolio.iterrows()} if not prev_portfolio.empty else {}
    curr_weights = {str(r["Code"]): float(r.get("TargetWeight", 0.0)) for _, r in current_portfolio.iterrows()}
    curr_prices = {str(r["Code"]): float(r.get("CurrentPrice", np.nan)) for _, r in current_portfolio.iterrows()}

    nav_before_cost = last_cash
    for code, prev_weight in prev_weights.items():
        prev_px = prev_prices.get(code, np.nan)
        curr_px = curr_prices.get(code, prev_px)
        if pd.notna(prev_px) and prev_px > 0 and pd.notna(curr_px) and curr_px > 0:
            nav_before_cost += last_nav * prev_weight * (curr_px / prev_px)
        else:
            nav_before_cost += last_nav * prev_weight

    if diff_df.empty:
        turnover = 0.0
    else:
        turnover = float(diff_df["WeightChange"].abs().sum())
    total_cost_rate = fee_rate + slippage_rate
    total_cost = nav_before_cost * turnover * total_cost_rate
    shadow_nav = max(nav_before_cost - total_cost, 0.0)
    gross_exposure = float(current_portfolio["TargetWeight"].sum()) if not current_portfolio.empty else 0.0
    cash = shadow_nav * max(0.0, 1.0 - gross_exposure)
    holdings_count = int(len(current_portfolio))

    ledger_rows = []
    if not diff_df.empty:
        for _, row in diff_df.iterrows():
            action = str(row["Action"])
            if action == "HOLD":
                continue
            code = str(row["Code"])
            weight_change = abs(float(row.get("WeightChange", 0.0)))
            fill_price = pick_fill_price(curr_prices.get(code, float(row.get("EstimatedPrice", np.nan))))
            notional = shadow_nav * weight_change
            fee_est = notional * fee_rate
            slip_est = notional * slippage_rate
            shares = notional / fill_price if pd.notna(fill_price) and fill_price > 0 else np.nan
            ledger_rows.append(
                {
                    "RunId": manifest.get("run_id"),
                    "RunStartedAt": manifest.get("started_at"),
                    "Strategy": strategy_name,
                    "TradeDate": meta["AsOfDate"],
                    "Code": code,
                    "Action": action,
                    "SignalWeight": float(row.get("NewWeight", 0.0)),
                    "AssumedFillPrice": fill_price,
                    "Shares": shares,
                    "Notional": notional,
                    "FeeEstimate": fee_est,
                    "SlippageEstimate": slip_est,
                    "Comment": "latest_close_fill_proxy",
                }
            )

    ledger_out = pd.concat([prev_ledger, pd.DataFrame(ledger_rows)], ignore_index=True) if not prev_ledger.empty else pd.DataFrame(ledger_rows)
    nav_row = pd.DataFrame(
        [
            {
                "Date": meta["AsOfDate"],
                "Strategy": strategy_name,
                "ShadowNAV": shadow_nav,
                "Cash": cash,
                "GrossExposure": gross_exposure,
                "HoldingsCount": holdings_count,
                "RunId": manifest.get("run_id"),
                "RunStartedAt": manifest.get("started_at"),
            }
        ]
    )
    nav_out = pd.concat([prev_nav, nav_row], ignore_index=True) if not prev_nav.empty else nav_row
    nav_out = nav_out.sort_values(["Date", "RunStartedAt"]).drop_duplicates(subset=["Date", "Strategy"], keep="last").reset_index(drop=True)

    write_csv_any(ledger_out, args.ledger_path, index=False)
    write_csv_any(nav_out, args.nav_path, index=False)
    print(f"saved {args.ledger_path}")
    print(f"saved {args.nav_path}")
    print(f"strategy={strategy_name} as_of={meta['AsOfDate']} shadow_nav={shadow_nav:.2f} turnover={turnover:.6f}")


if __name__ == "__main__":
    main()
