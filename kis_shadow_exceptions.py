import argparse

import pandas as pd

import config
from kis_backtest_from_prices import write_csv_any
from kis_shadow_common import default_backtests_base, read_csv_any, read_json_any, resolve_strategy_name


def add_row(rows: list[dict], run_id: str, run_started_at: str, strategy: str, as_of_date: str, severity: str, category: str, metric: str, value, threshold, message: str) -> None:
    rows.append(
        {
            "RunId": run_id,
            "RunStartedAt": run_started_at,
            "Strategy": strategy,
            "AsOfDate": as_of_date,
            "Severity": severity,
            "Category": category,
            "Metric": metric,
            "Value": value,
            "Threshold": threshold,
            "Message": message,
        }
    )


def main() -> None:
    default_base = default_backtests_base()
    p = argparse.ArgumentParser(description="Emit row-level shadow exceptions for the latest run.")
    p.add_argument("--live-readiness-path", type=str, default=f"{default_base}/kis_live_readiness.csv")
    p.add_argument("--manifest-path", type=str, default=f"{default_base}/kis_pipeline_run_manifest.json")
    p.add_argument("--health-path", type=str, default=f"{default_base}/kis_shadow_health.csv")
    p.add_argument("--ops-summary-path", type=str, default=f"{default_base}/kis_shadow_ops_summary.csv")
    p.add_argument("--portfolio-path", type=str, default=f"{default_base}/kis_shadow_portfolio.csv")
    p.add_argument("--nav-path", type=str, default=f"{default_base}/kis_shadow_nav.csv")
    p.add_argument("--save-path", type=str, default=f"{default_base}/kis_shadow_exceptions.csv")
    p.add_argument("--strategy-name", type=str, default="")
    args = p.parse_args()

    manifest = read_json_any(args.manifest_path)
    health = read_csv_any(args.health_path)
    ops = read_csv_any(args.ops_summary_path)
    portfolio = read_csv_any(args.portfolio_path)
    nav_df = read_csv_any(args.nav_path)

    strategy_name = resolve_strategy_name(args.live_readiness_path, args.strategy_name or None)
    if not health.empty and "Strategy" in health.columns:
        health = health[health["Strategy"].astype(str) == strategy_name].copy()
    if not ops.empty and "Strategy" in ops.columns:
        ops = ops[ops["Strategy"].astype(str) == strategy_name].copy()
    if not portfolio.empty and "Strategy" in portfolio.columns:
        portfolio = portfolio[portfolio["Strategy"].astype(str) == strategy_name].copy()
    if not nav_df.empty and "Strategy" in nav_df.columns:
        nav_df = nav_df[nav_df["Strategy"].astype(str) == strategy_name].copy()

    run_id = str(manifest.get("run_id", ""))
    run_started_at = str(manifest.get("started_at", ""))
    as_of_date = str(ops.iloc[-1]["AsOfDate"]) if not ops.empty else ""
    health_row = health.iloc[-1] if not health.empty else pd.Series(dtype=object)
    ops_row = ops.iloc[-1] if not ops.empty else pd.Series(dtype=object)
    latest_nav = nav_df.sort_values(["Date", "RunStartedAt"]).iloc[-1] if not nav_df.empty else pd.Series(dtype=object)

    rows: list[dict] = []
    add_row(rows, run_id, run_started_at, strategy_name, as_of_date, "INFO", "HEALTH", "DailyCheckStatus", str(ops_row.get("DailyCheckStatus", "")), "GO", "daily shadow monitoring row")

    health_status = str(health_row.get("HealthStatus", ""))
    if health_status in {"STALE", "ERROR"}:
        add_row(rows, run_id, run_started_at, strategy_name, as_of_date, "ERROR", "HEALTH", "HealthStatus", health_status, "OK", "shadow health is not operationally safe")
    elif health_status == "WARNING":
        add_row(rows, run_id, run_started_at, strategy_name, as_of_date, "WARNING", "HEALTH", "HealthStatus", health_status, "OK", "shadow health requires review")

    source_fresh = int(float(health_row.get("SourceFresh", 0) or 0))
    if source_fresh != 1:
        add_row(rows, run_id, run_started_at, strategy_name, as_of_date, "ERROR", "FRESHNESS", "SourceFresh", source_fresh, 1, "source artifacts do not match current run id")

    missing_price_count = int(float(health_row.get("MissingPriceCount", 0) or 0))
    if missing_price_count > 0:
        sev = "ERROR" if missing_price_count >= 3 else "WARNING"
        add_row(rows, run_id, run_started_at, strategy_name, as_of_date, sev, "PRICES", "MissingPriceCount", missing_price_count, 0, "portfolio contains missing prices")

    weight_sum = float(health_row.get("WeightSum", 0.0) or 0.0)
    if weight_sum < -1e-9 or weight_sum > 1.05:
        add_row(rows, run_id, run_started_at, strategy_name, as_of_date, "ERROR", "WEIGHTS", "WeightSum", weight_sum, "[0,1.05]", "portfolio gross weight is outside expected bounds")
    elif portfolio.empty:
        add_row(rows, run_id, run_started_at, strategy_name, as_of_date, "ERROR", "PORTFOLIO", "PortfolioRowCount", 0, ">0", "shadow portfolio is empty")

    turnover_est = float(health_row.get("TurnoverEstimate", 0.0) or 0.0)
    if turnover_est >= 0.50:
        add_row(rows, run_id, run_started_at, strategy_name, as_of_date, "WARNING", "TURNOVER", "TurnoverEstimate", turnover_est, "<0.50", "turnover is materially large")

    recommended_match = int(float(health_row.get("RecommendedStrategyMatch", 0) or 0))
    if recommended_match != 1:
        add_row(rows, run_id, run_started_at, strategy_name, as_of_date, "WARNING", "STRATEGY_MATCH", "RecommendedStrategyMatch", recommended_match, 1, "selected strategy differs from current recommended strategy")

    shadow_nav = float(latest_nav.get("ShadowNAV", 0.0) or 0.0)
    if shadow_nav <= 0:
        add_row(rows, run_id, run_started_at, strategy_name, as_of_date, "ERROR", "NAV", "ShadowNAV", shadow_nav, ">0", "shadow nav is non-positive")

    out = pd.DataFrame(rows)
    write_csv_any(out, args.save_path, index=False)
    print(f"saved {args.save_path}")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
