from __future__ import annotations

from pathlib import Path


BACKTESTS_DIRNAME = "backtests"

BASELINE_PREFIX = "kis_bt_auto"
BASELINE_SUMMARY_FILENAME = "kis_bt_auto_summary.csv"
BASELINE_NAV_FILENAME = "kis_bt_auto_nav.csv"
DATA_COVERAGE_FILENAME = "kis_data_coverage_report.csv"
PARAM_GRID_FILENAME = "kis_param_grid_results.csv"
WALKFORWARD_RESULTS_FILENAME = "kis_walkforward_results.csv"
WALKFORWARD_SUMMARY_FILENAME = "kis_walkforward_summary.csv"
COST_SENSITIVITY_FILENAME = "kis_bt_cost_sensitivity_extended.csv"
COST_STRESS_REPORT_FILENAME = "kis_cost_stress_report.csv"
LEADERBOARD_FILENAME = "kis_strategy_leaderboard.csv"
LIVE_READINESS_FILENAME = "kis_live_readiness.csv"
SLEEVE_ATTRIBUTION_REPORT_FILENAME = "kis_sleeve_attribution_report.csv"
SLEEVE_COMPARE_REPORT_FILENAME = "kis_sleeve_compare_report.csv"
SHADOW_PORTFOLIO_FILENAME = "kis_shadow_portfolio.csv"
SHADOW_REBALANCE_DIFF_FILENAME = "kis_shadow_rebalance_diff.csv"
SHADOW_LEDGER_FILENAME = "kis_shadow_ledger.csv"
SHADOW_NAV_FILENAME = "kis_shadow_nav.csv"
SHADOW_HEALTH_FILENAME = "kis_shadow_health.csv"
SHADOW_OPS_SUMMARY_FILENAME = "kis_shadow_ops_summary.csv"
SHADOW_EXCEPTIONS_FILENAME = "kis_shadow_exceptions.csv"
RUN_MANIFEST_FILENAME = "kis_pipeline_run_manifest.json"


def _strip_trailing_slash(path: str) -> str:
    return path.rstrip("/\\")


def join_output_path(output_base: str, filename: str) -> str:
    base = _strip_trailing_slash(output_base)
    if base.startswith("gs://"):
        return f"{base}/{filename}"
    return str(Path(base) / filename)


def baseline_save_prefix(output_base: str) -> str:
    return join_output_path(output_base, BASELINE_PREFIX)


def baseline_summary_path(output_base: str) -> str:
    return join_output_path(output_base, BASELINE_SUMMARY_FILENAME)


def baseline_nav_path(output_base: str) -> str:
    return join_output_path(output_base, BASELINE_NAV_FILENAME)


def data_coverage_path(output_base: str) -> str:
    return join_output_path(output_base, DATA_COVERAGE_FILENAME)


def param_grid_path(output_base: str) -> str:
    return join_output_path(output_base, PARAM_GRID_FILENAME)


def walkforward_results_path(output_base: str) -> str:
    return join_output_path(output_base, WALKFORWARD_RESULTS_FILENAME)


def walkforward_summary_path(output_base: str) -> str:
    return join_output_path(output_base, WALKFORWARD_SUMMARY_FILENAME)


def cost_sensitivity_path(output_base: str) -> str:
    return join_output_path(output_base, COST_SENSITIVITY_FILENAME)


def leaderboard_path(output_base: str) -> str:
    return join_output_path(output_base, LEADERBOARD_FILENAME)


def cost_stress_report_path(output_base: str) -> str:
    return join_output_path(output_base, COST_STRESS_REPORT_FILENAME)


def live_readiness_path(output_base: str) -> str:
    return join_output_path(output_base, LIVE_READINESS_FILENAME)


def sleeve_attribution_report_path(output_base: str) -> str:
    return join_output_path(output_base, SLEEVE_ATTRIBUTION_REPORT_FILENAME)


def sleeve_compare_report_path(output_base: str) -> str:
    return join_output_path(output_base, SLEEVE_COMPARE_REPORT_FILENAME)


def shadow_portfolio_path(output_base: str) -> str:
    return join_output_path(output_base, SHADOW_PORTFOLIO_FILENAME)


def shadow_rebalance_diff_path(output_base: str) -> str:
    return join_output_path(output_base, SHADOW_REBALANCE_DIFF_FILENAME)


def shadow_ledger_path(output_base: str) -> str:
    return join_output_path(output_base, SHADOW_LEDGER_FILENAME)


def shadow_nav_path(output_base: str) -> str:
    return join_output_path(output_base, SHADOW_NAV_FILENAME)


def shadow_health_path(output_base: str) -> str:
    return join_output_path(output_base, SHADOW_HEALTH_FILENAME)


def shadow_ops_summary_path(output_base: str) -> str:
    return join_output_path(output_base, SHADOW_OPS_SUMMARY_FILENAME)


def shadow_exceptions_path(output_base: str) -> str:
    return join_output_path(output_base, SHADOW_EXCEPTIONS_FILENAME)


def run_manifest_path(output_base: str) -> str:
    return join_output_path(output_base, RUN_MANIFEST_FILENAME)


def canonical_artifact_paths(output_base: str) -> dict[str, str]:
    return {
        "baseline_summary": baseline_summary_path(output_base),
        "baseline_nav": baseline_nav_path(output_base),
        "data_coverage": data_coverage_path(output_base),
        "param_grid": param_grid_path(output_base),
        "walkforward_results": walkforward_results_path(output_base),
        "walkforward_summary": walkforward_summary_path(output_base),
        "cost_sensitivity": cost_sensitivity_path(output_base),
        "cost_stress_report": cost_stress_report_path(output_base),
        "leaderboard": leaderboard_path(output_base),
        "live_readiness": live_readiness_path(output_base),
        "sleeve_attribution_report": sleeve_attribution_report_path(output_base),
        "sleeve_compare_report": sleeve_compare_report_path(output_base),
        "shadow_portfolio": shadow_portfolio_path(output_base),
        "shadow_rebalance_diff": shadow_rebalance_diff_path(output_base),
        "shadow_ledger": shadow_ledger_path(output_base),
        "shadow_nav": shadow_nav_path(output_base),
        "shadow_health": shadow_health_path(output_base),
        "shadow_ops_summary": shadow_ops_summary_path(output_base),
        "shadow_exceptions": shadow_exceptions_path(output_base),
        "run_manifest": run_manifest_path(output_base),
    }
