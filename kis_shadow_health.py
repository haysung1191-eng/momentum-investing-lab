import argparse

import numpy as np
import pandas as pd

import config
from kis_backtest_from_prices import write_csv_any
from kis_shadow_common import default_backtests_base, read_csv_any, read_json_any, resolve_strategy_name


def main() -> None:
    default_base = default_backtests_base()
    p = argparse.ArgumentParser(description="Build a compact shadow-operation health report.")
    p.add_argument("--live-readiness-path", type=str, default=f"{default_base}/kis_live_readiness.csv")
    p.add_argument("--manifest-path", type=str, default=f"{default_base}/kis_pipeline_run_manifest.json")
    p.add_argument("--portfolio-path", type=str, default=f"{default_base}/kis_shadow_portfolio.csv")
    p.add_argument("--diff-path", type=str, default=f"{default_base}/kis_shadow_rebalance_diff.csv")
    p.add_argument("--save-path", type=str, default=f"{default_base}/kis_shadow_health.csv")
    p.add_argument("--strategy-name", type=str, default="")
    p.add_argument("--material-change-threshold", type=float, default=0.10)
    args = p.parse_args()

    manifest = read_json_any(args.manifest_path)
    ready = read_csv_any(args.live_readiness_path)
    portfolio = read_csv_any(args.portfolio_path)
    diff_df = read_csv_any(args.diff_path)

    strategy_name = resolve_strategy_name(args.live_readiness_path, args.strategy_name or None)
    ready_row = pd.DataFrame()
    if not ready.empty and "Strategy" in ready.columns:
        ready_row = ready[ready["Strategy"].astype(str) == strategy_name].copy()
    if not portfolio.empty and "Strategy" in portfolio.columns:
        portfolio = portfolio[portfolio["Strategy"].astype(str) == strategy_name].copy()
    if not diff_df.empty and "Strategy" in diff_df.columns:
        diff_df = diff_df[diff_df["Strategy"].astype(str) == strategy_name].copy()

    source_fresh = False
    if not portfolio.empty and "RunId" in portfolio.columns:
        source_fresh = portfolio["RunId"].astype(str).eq(str(manifest.get("run_id"))).all()
    readiness_fresh = False
    readiness_run_id = ""
    readiness_operational_status = ""
    if not ready_row.empty:
        readiness_run_id = str(ready_row.iloc[-1].get("RunId", "") or "")
        readiness_operational_status = str(ready_row.iloc[-1].get("OperationalStatus", "") or "")
        readiness_fresh = bool(readiness_run_id) and readiness_run_id == str(manifest.get("run_id")) and readiness_operational_status == "fresh"

    recommended_strategy = resolve_strategy_name(args.live_readiness_path, None)
    recommended_match = int(strategy_name == recommended_strategy)
    missing_price_count = int(((pd.to_numeric(portfolio.get("CurrentPrice"), errors="coerce") <= 0) | portfolio.get("CurrentPrice").isna()).sum()) if not portfolio.empty else 0
    weight_sum = float(pd.to_numeric(portfolio.get("TargetWeight"), errors="coerce").fillna(0.0).sum()) if not portfolio.empty else 0.0
    regime_state = str(portfolio["RegimeState"].iloc[0]) if not portfolio.empty and "RegimeState" in portfolio.columns else ""
    turnover_est = float(pd.to_numeric(diff_df.get("WeightChange"), errors="coerce").fillna(0.0).abs().sum()) if not diff_df.empty else 0.0
    material_change = int(turnover_est >= args.material_change_threshold)
    as_of_date = ""
    if not portfolio.empty and "AsOfDate" in portfolio.columns:
        as_of_date = str(portfolio["AsOfDate"].iloc[0])

    if portfolio.empty:
        health_status = "ERROR"
        recommendation = "NO_PORTFOLIO_OUTPUT"
    elif not source_fresh or not readiness_fresh:
        health_status = "STALE"
        recommendation = "RERUN_PIPELINE"
    elif missing_price_count > 0 or weight_sum < -1e-9 or weight_sum > 1.05 or (regime_state != "risk_off" and weight_sum < 0.25):
        health_status = "WARNING"
        recommendation = "REVIEW_PRICES_AND_WEIGHTS"
    elif not recommended_match:
        health_status = "WARNING"
        recommendation = "REVIEW_STRATEGY_SELECTION"
    else:
        health_status = "OK"
        recommendation = "READY_FOR_DAILY_SHADOW_CHECK"

    out = pd.DataFrame(
        [
            {
                "RunId": manifest.get("run_id"),
                "RunStartedAt": manifest.get("started_at"),
                "Strategy": strategy_name,
                "AsOfDate": as_of_date,
                "SourceFresh": int(source_fresh),
                "ReadinessFresh": int(readiness_fresh),
                "ReadinessRunId": readiness_run_id,
                "ReadinessOperationalStatus": readiness_operational_status,
                "RecommendedStrategyMatch": recommended_match,
                "MissingPriceCount": missing_price_count,
                "WeightSum": weight_sum,
                "TurnoverEstimate": turnover_est,
                "MaterialChange": material_change,
                "HealthStatus": health_status,
                "Recommendation": recommendation,
            }
        ]
    )
    write_csv_any(out, args.save_path, index=False)
    print(f"saved {args.save_path}")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
