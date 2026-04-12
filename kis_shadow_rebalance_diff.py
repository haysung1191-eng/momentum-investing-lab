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


def classify_action(prev_weight: float, new_weight: float) -> str:
    if prev_weight <= 1e-12 and new_weight > 1e-12:
        return "BUY"
    if prev_weight > 1e-12 and new_weight <= 1e-12:
        return "EXIT"
    if new_weight > prev_weight + 1e-12:
        return "INCREASE"
    if new_weight < prev_weight - 1e-12:
        return "DECREASE"
    return "HOLD"


def main() -> None:
    default_base = default_backtests_base()
    p = argparse.ArgumentParser(description="Compare current target portfolio to the previous shadow portfolio artifact.")
    p.add_argument("--base", type=str, default=(f"gs://{config.GCS_BUCKET_NAME}/prices" if config.GCS_BUCKET_NAME else "data/prices"))
    p.add_argument("--live-readiness-path", type=str, default=f"{default_base}/kis_live_readiness.csv")
    p.add_argument("--manifest-path", type=str, default=f"{default_base}/kis_pipeline_run_manifest.json")
    p.add_argument("--current-portfolio-path", type=str, default="")
    p.add_argument("--previous-portfolio-path", type=str, default=f"{default_base}/kis_shadow_portfolio.csv")
    p.add_argument("--save-path", type=str, default=f"{default_base}/kis_shadow_rebalance_diff.csv")
    p.add_argument("--strategy-name", type=str, default="")
    p.add_argument("--as-of-date", type=str, default="")
    p.add_argument("--min-common-dates", type=int, default=180)
    p.add_argument("--max-files", type=int, default=0)
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
    previous_portfolio = read_csv_any(args.previous_portfolio_path) if args.previous_portfolio_path else pd.DataFrame()
    if not previous_portfolio.empty and "Strategy" in previous_portfolio.columns:
        previous_portfolio = previous_portfolio[previous_portfolio["Strategy"].astype(str) == strategy_name].copy()

    prev_map = {}
    if not previous_portfolio.empty:
        for _, row in previous_portfolio.iterrows():
            prev_map[str(row["Code"])] = {
                "PrevWeight": float(row.get("TargetWeight", 0.0)),
                "EstimatedPrice": float(row.get("CurrentPrice", np.nan)),
            }
    curr_map = {}
    for _, row in current_portfolio.iterrows():
        curr_map[str(row["Code"])] = {
            "NewWeight": float(row.get("TargetWeight", 0.0)),
            "EstimatedPrice": float(row.get("CurrentPrice", np.nan)),
        }

    codes = sorted(set(prev_map) | set(curr_map))
    rows = []
    for code in codes:
        prev_weight = float(prev_map.get(code, {}).get("PrevWeight", 0.0))
        new_weight = float(curr_map.get(code, {}).get("NewWeight", 0.0))
        est_price = curr_map.get(code, {}).get("EstimatedPrice", prev_map.get(code, {}).get("EstimatedPrice", np.nan))
        action = classify_action(prev_weight, new_weight)
        rows.append(
            {
                "RunId": manifest.get("run_id"),
                "RunStartedAt": manifest.get("started_at"),
                "Strategy": strategy_name,
                "AsOfDate": meta["AsOfDate"],
                "Code": code,
                "PrevWeight": prev_weight,
                "NewWeight": new_weight,
                "WeightChange": new_weight - prev_weight,
                "Action": action,
                "EstimatedPrice": est_price,
                "Notes": "initial_snapshot" if previous_portfolio.empty else "",
            }
        )

    out = pd.DataFrame(rows)
    write_csv_any(out, args.save_path, index=False)
    print(f"saved {args.save_path}")
    print(f"strategy={strategy_name} as_of={meta['AsOfDate']} changes={int((out['Action'] != 'HOLD').sum()) if not out.empty else 0}")
    print("\n=== Shadow Rebalance Diff ===")
    print(out.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
