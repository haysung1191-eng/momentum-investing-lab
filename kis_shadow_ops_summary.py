import argparse

import pandas as pd

import config
from kis_backtest_from_prices import write_csv_any
from kis_shadow_common import default_backtests_base, read_csv_any, read_json_any, resolve_strategy_name


def count_action(diff_df: pd.DataFrame, action: str) -> int:
    if diff_df.empty or "Action" not in diff_df.columns:
        return 0
    return int(diff_df["Action"].astype(str).eq(action).sum())


def main() -> None:
    default_base = default_backtests_base()
    p = argparse.ArgumentParser(description="Build a one-row daily shadow operations summary.")
    p.add_argument("--live-readiness-path", type=str, default=f"{default_base}/kis_live_readiness.csv")
    p.add_argument("--manifest-path", type=str, default=f"{default_base}/kis_pipeline_run_manifest.json")
    p.add_argument("--health-path", type=str, default=f"{default_base}/kis_shadow_health.csv")
    p.add_argument("--diff-path", type=str, default=f"{default_base}/kis_shadow_rebalance_diff.csv")
    p.add_argument("--portfolio-path", type=str, default=f"{default_base}/kis_shadow_portfolio.csv")
    p.add_argument("--nav-path", type=str, default=f"{default_base}/kis_shadow_nav.csv")
    p.add_argument("--save-path", type=str, default=f"{default_base}/kis_shadow_ops_summary.csv")
    p.add_argument("--strategy-name", type=str, default="")
    args = p.parse_args()

    manifest = read_json_any(args.manifest_path)
    live = read_csv_any(args.live_readiness_path)
    health = read_csv_any(args.health_path)
    diff_df = read_csv_any(args.diff_path)
    portfolio = read_csv_any(args.portfolio_path)
    nav_df = read_csv_any(args.nav_path)

    strategy_name = resolve_strategy_name(args.live_readiness_path, args.strategy_name or None)
    live_row = pd.DataFrame()
    if not live.empty and "Strategy" in live.columns:
        live_row = live[live["Strategy"].astype(str) == strategy_name].copy()
    if not health.empty and "Strategy" in health.columns:
        health = health[health["Strategy"].astype(str) == strategy_name].copy()
    if not diff_df.empty and "Strategy" in diff_df.columns:
        diff_df = diff_df[diff_df["Strategy"].astype(str) == strategy_name].copy()
    if not portfolio.empty and "Strategy" in portfolio.columns:
        portfolio = portfolio[portfolio["Strategy"].astype(str) == strategy_name].copy()
    if not nav_df.empty and "Strategy" in nav_df.columns:
        nav_df = nav_df[nav_df["Strategy"].astype(str) == strategy_name].copy()

    recommended_strategy = resolve_strategy_name(args.live_readiness_path, None)
    recommended_strategy_match = int(strategy_name == recommended_strategy)
    readiness_run_id = str(live_row.iloc[-1].get("RunId", "")) if not live_row.empty else ""
    manifest_run_id = str(manifest.get("run_id", "") or "")
    readiness_run_match = int(bool(readiness_run_id) and readiness_run_id == manifest_run_id)

    latest_nav = nav_df.sort_values(["Date", "RunStartedAt"]).iloc[-1] if not nav_df.empty else pd.Series(dtype=object)
    health_row = health.iloc[-1] if not health.empty else pd.Series(dtype=object)

    portfolio_row_count = int(len(portfolio))
    holdings_count = int(portfolio["Code"].nunique()) if not portfolio.empty and "Code" in portfolio.columns else 0
    weight_sum = float(pd.to_numeric(portfolio.get("TargetWeight"), errors="coerce").fillna(0.0).sum()) if not portfolio.empty else 0.0
    turnover_est = float(pd.to_numeric(diff_df.get("WeightChange"), errors="coerce").fillna(0.0).abs().sum()) if not diff_df.empty else float(health_row.get("TurnoverEstimate", 0.0) or 0.0)
    material_change = int(float(health_row.get("MaterialChange", 0) or 0))
    missing_price_count = int(float(health_row.get("MissingPriceCount", 0) or 0))
    health_status = str(health_row.get("HealthStatus", "ERROR") or "ERROR")
    recommendation = str(health_row.get("Recommendation", "NO_HEALTH_OUTPUT") or "NO_HEALTH_OUTPUT")
    as_of_date = str(health_row.get("AsOfDate", "")) if not health.empty else (str(portfolio["AsOfDate"].iloc[0]) if not portfolio.empty and "AsOfDate" in portfolio.columns else "")

    if health_status in {"STALE", "ERROR"} or portfolio_row_count <= 0 or readiness_run_match == 0:
        daily_status = "STOP"
        daily_comment = "critical_shadow_issue"
    elif health_status == "WARNING" or material_change == 1 or missing_price_count > 0 or turnover_est >= 0.25:
        daily_status = "REVIEW"
        daily_comment = "review_shadow_changes"
    else:
        daily_status = "GO"
        daily_comment = "daily_shadow_ok"

    out = pd.DataFrame(
        [
            {
                "RunId": manifest.get("run_id"),
                "RunStartedAt": manifest.get("started_at"),
                "Strategy": strategy_name,
                "AsOfDate": as_of_date,
                "HealthStatus": health_status,
                "Recommendation": recommendation,
                "RecommendedStrategy": recommended_strategy,
                "RecommendedStrategyMatch": recommended_strategy_match,
                "ReadinessRunId": readiness_run_id,
                "ReadinessRunMatch": readiness_run_match,
                "PortfolioRowCount": portfolio_row_count,
                "HoldingsCount": holdings_count,
                "WeightSum": weight_sum,
                "TurnoverEstimate": turnover_est,
                "MaterialChange": material_change,
                "MissingPriceCount": missing_price_count,
                "DiffBuyCount": count_action(diff_df, "BUY"),
                "DiffExitCount": count_action(diff_df, "EXIT"),
                "DiffIncreaseCount": count_action(diff_df, "INCREASE"),
                "DiffDecreaseCount": count_action(diff_df, "DECREASE"),
                "DiffHoldCount": count_action(diff_df, "HOLD"),
                "ShadowNAV": float(latest_nav.get("ShadowNAV", 0.0) or 0.0),
                "Cash": float(latest_nav.get("Cash", 0.0) or 0.0),
                "GrossExposure": float(latest_nav.get("GrossExposure", 0.0) or 0.0),
                "DailyCheckStatus": daily_status,
                "DailyCheckComment": daily_comment,
            }
        ]
    )
    write_csv_any(out, args.save_path, index=False)
    print(f"saved {args.save_path}")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
