from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

from google.cloud import storage
import pandas as pd

from app.artifacts import contract


ROOT = Path(__file__).resolve().parents[2]
TRACEABILITY_ARTIFACT_KEYS = {
    "baseline_summary",
    "data_coverage",
    "param_grid",
    "walkforward_results",
    "walkforward_summary",
    "cost_sensitivity",
    "cost_stress_report",
    "leaderboard",
    "live_readiness",
    "sleeve_attribution_report",
    "sleeve_compare_report",
    "shadow_portfolio",
    "shadow_rebalance_diff",
    "shadow_ledger",
    "shadow_nav",
    "shadow_health",
    "shadow_ops_summary",
    "shadow_exceptions",
}


@dataclass(frozen=True)
class StepSpec:
    name: str
    script: str
    args: list[str]
    expected_artifacts: list[str]
    skipped: bool = False


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run the canonical KIS research pipeline via existing script entrypoints.")
    p.add_argument("--base", type=str, required=True, help="Input price base path (local dir or gs:// bucket path).")
    p.add_argument("--output-base", type=str, required=True, help="Output artifact base path (local dir or gs:// bucket path).")
    p.add_argument("--workers", type=int, default=1)
    p.add_argument("--min-common-dates", type=int, default=180)
    p.add_argument("--train-years", type=int, default=8)
    p.add_argument("--test-years", type=int, default=2)
    p.add_argument("--step-years", type=int, default=1)
    p.add_argument("--min-oos-windows", type=int, default=3)
    p.add_argument("--roundtrip-costs", type=str, default="0.20,0.35,0.50,0.60,0.80,1.00")
    p.add_argument("--skip-backfill", action="store_true")
    p.add_argument("--skip-baseline", action="store_true")
    p.add_argument("--skip-coverage", action="store_true")
    p.add_argument("--skip-grid", action="store_true")
    p.add_argument("--skip-walkforward", action="store_true")
    p.add_argument("--skip-cost", action="store_true")
    p.add_argument("--skip-cost-stress-report", action="store_true")
    p.add_argument("--skip-leaderboard", action="store_true")
    p.add_argument("--skip-live-readiness", action="store_true")
    p.add_argument("--skip-sleeve-report", action="store_true")
    p.add_argument("--skip-sleeve-compare", action="store_true")
    p.add_argument("--skip-shadow-portfolio", action="store_true")
    p.add_argument("--skip-shadow-diff", action="store_true")
    p.add_argument("--skip-shadow-performance", action="store_true")
    p.add_argument("--skip-shadow-health", action="store_true")
    p.add_argument("--skip-shadow-ops-summary", action="store_true")
    p.add_argument("--skip-shadow-exceptions", action="store_true")
    p.add_argument("--strategy-name", type=str, default="")
    p.add_argument("--shadow-starting-capital", type=float, default=10_000_000.0)
    p.add_argument("--shadow-one-way-fee-bps", type=float, default=10.0)
    p.add_argument("--shadow-one-way-slippage-bps", type=float, default=15.0)
    p.add_argument("--shadow-material-change-threshold", type=float, default=0.10)
    p.add_argument("--backfill-mode", choices=["stock", "etf", "both"], default="both")
    p.add_argument("--backfill-years", type=int, default=5)
    p.add_argument("--incremental-days", type=int, default=35)
    p.add_argument("--max-items", type=int, default=500)
    p.add_argument("--sleep-sec", type=float, default=0.05)
    p.add_argument("--historical-stock-universe", type=int, default=1)
    p.add_argument("--top-n", type=int, default=20)
    p.add_argument("--fee-bps", type=int, default=8)
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
    return p.parse_args()


def _parse_gcs_uri(path: str) -> tuple[str, str]:
    if not path.startswith("gs://"):
        raise ValueError(f"Not a GCS path: {path}")
    without_scheme = path[5:]
    bucket, _, blob = without_scheme.partition("/")
    return bucket, blob


def ensure_parent_dir(path: str) -> None:
    if path.startswith("gs://"):
        return
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def ensure_step_output_dirs(step: StepSpec) -> None:
    for path in step.expected_artifacts:
        ensure_parent_dir(path)
    if step.name == "baseline":
        save_prefix = step.args[step.args.index("--save-prefix") + 1]
        ensure_parent_dir(f"{save_prefix}_summary.csv")


def path_exists(path: str) -> bool:
    if path.startswith("gs://"):
        bucket_name, blob_name = _parse_gcs_uri(path)
        client = storage.Client()
        return client.bucket(bucket_name).blob(blob_name).exists(client)
    return Path(path).exists()


def write_json_any(data: dict[str, Any], path: str) -> None:
    ensure_parent_dir(path)
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    if path.startswith("gs://"):
        bucket_name, blob_name = _parse_gcs_uri(path)
        client = storage.Client()
        client.bucket(bucket_name).blob(blob_name).upload_from_string(payload, content_type="application/json")
        return
    Path(path).write_text(payload, encoding="utf-8")


def copy_to_local_if_exists(src_path: str, dst_path: str) -> str | None:
    if not path_exists(src_path):
        return None
    ensure_parent_dir(dst_path)
    if src_path.startswith("gs://"):
        bucket_name, blob_name = _parse_gcs_uri(src_path)
        client = storage.Client()
        payload = client.bucket(bucket_name).blob(blob_name).download_as_bytes()
        Path(dst_path).write_bytes(payload)
        return dst_path
    Path(dst_path).write_bytes(Path(src_path).read_bytes())
    return dst_path


def build_run_id(started_at: datetime) -> str:
    return f"{started_at.strftime('%Y%m%dT%H%M%SZ')}_kis_pipeline"


def read_csv_any(path: str) -> pd.DataFrame:
    if path.startswith("gs://"):
        bucket_name, blob_name = _parse_gcs_uri(path)
        client = storage.Client()
        text = client.bucket(bucket_name).blob(blob_name).download_as_text(encoding="utf-8")
        return pd.read_csv(io.StringIO(text))
    return pd.read_csv(path)


def write_csv_any(df: pd.DataFrame, path: str) -> None:
    ensure_parent_dir(path)
    payload = df.to_csv(index=False)
    if path.startswith("gs://"):
        bucket_name, blob_name = _parse_gcs_uri(path)
        client = storage.Client()
        client.bucket(bucket_name).blob(blob_name).upload_from_string(payload, content_type="text/csv")
        return
    Path(path).write_text(payload, encoding="utf-8", newline="")


def annotate_csv_artifact(path: str, run_id: str, run_started_at: str) -> None:
    try:
        df = read_csv_any(path)
    except pd.errors.EmptyDataError:
        df = pd.DataFrame(columns=["RunId", "RunStartedAt"])

    df["RunId"] = run_id
    df["RunStartedAt"] = run_started_at
    write_csv_any(df, path)


def annotate_step_artifacts(step: StepSpec, artifacts: dict[str, str], run_id: str, run_started_at: str) -> list[str]:
    traceable_paths = {
        artifacts[key]
        for key in TRACEABILITY_ARTIFACT_KEYS
        if key in artifacts
    }
    annotated: list[str] = []
    for path in step.expected_artifacts:
        if path not in traceable_paths:
            continue
        annotate_csv_artifact(path, run_id, run_started_at)
        annotated.append(path)
    return annotated


def finalize_manifest(
    manifest: dict[str, Any],
    manifest_path: str,
    started_at: datetime,
    started_perf: float,
    final_status: str,
    failed_step: str | None,
) -> None:
    finished_at = datetime.now(timezone.utc)
    manifest["started_at"] = started_at.isoformat()
    manifest["finished_at"] = finished_at.isoformat()
    manifest["duration_seconds"] = round(perf_counter() - started_perf, 3)
    manifest["final_status"] = final_status
    manifest["failed_step"] = failed_step
    write_json_any(manifest, manifest_path)


def build_steps(args: argparse.Namespace, previous_shadow_portfolio_path: str | None = None) -> list[StepSpec]:
    artifacts = contract.canonical_artifact_paths(args.output_base)
    baseline_prefix = contract.baseline_save_prefix(args.output_base)
    param_grid_workers = args.workers
    if os.name == "nt" and args.base.startswith("gs://") and args.workers > 1:
        param_grid_workers = 1
        print("param_grid worker override: using workers=1 on Windows + GCS to avoid spawn/reload bottlenecks.")
    return [
        StepSpec(
            name="backfill",
            script="kis_data_backfill.py",
            args=[
                "--mode", args.backfill_mode,
                "--years", str(args.backfill_years),
                "--incremental-days", str(args.incremental_days),
                "--max-items", str(args.max_items),
                "--out-base", args.base,
                "--sleep-sec", str(args.sleep_sec),
                "--historical-stock-universe", str(args.historical_stock_universe),
            ],
            expected_artifacts=[],
            skipped=args.skip_backfill,
        ),
        StepSpec(
            name="baseline",
            script="kis_backtest_from_prices.py",
            args=[
                "--base", args.base,
                "--top-n", str(args.top_n),
                "--fee-bps", str(args.fee_bps),
                "--min-common-dates", str(args.min_common_dates),
                "--save-prefix", baseline_prefix,
                "--regime-filter", str(args.regime_filter),
                "--stop-loss-pct", str(args.stop_loss_pct),
                "--trend-exit-ma", str(args.trend_exit_ma),
                "--regime-ma-window", str(args.regime_ma_window),
                "--regime-slope-window", str(args.regime_slope_window),
                "--regime-breadth-threshold", str(args.regime_breadth_threshold),
                "--vol-lookback", str(args.vol_lookback),
                "--target-vol-annual", str(args.target_vol_annual),
                "--max-weight", str(args.max_weight),
                "--min-gross-exposure", str(args.min_gross_exposure),
                "--score-top-k", str(args.score_top_k),
                "--score-power", str(args.score_power),
                "--regime-off-exposure", str(args.regime_off_exposure),
                "--allow-intraperiod-reentry", str(args.allow_intraperiod_reentry),
                "--reentry-cooldown-days", str(args.reentry_cooldown_days),
                "--osc-lookback", str(args.osc_lookback),
                "--osc-z-entry", str(args.osc_z_entry),
                "--osc-z-exit", str(args.osc_z_exit),
                "--osc-z-stop", str(args.osc_z_stop),
                "--osc-band-sigma", str(args.osc_band_sigma),
                "--osc-band-break-sigma", str(args.osc_band_break_sigma),
                "--osc-reentry-cooldown-days", str(args.osc_reentry_cooldown_days),
                "--rotation-top-k", str(args.rotation_top_k),
                "--rotation-tilt-strength", str(args.rotation_tilt_strength),
                "--rotation-min-sleeve-weight", str(args.rotation_min_sleeve_weight),
                "--range-slope-threshold", str(args.range_slope_threshold),
                "--range-dist-threshold", str(args.range_dist_threshold),
                "--range-breakout-persistence-threshold", str(args.range_breakout_persistence_threshold),
                "--range-breadth-tolerance", str(args.range_breadth_tolerance),
            ],
            expected_artifacts=[artifacts["baseline_summary"], artifacts["baseline_nav"]],
            skipped=args.skip_baseline,
        ),
        StepSpec(
            name="coverage",
            script="kis_data_coverage.py",
            args=["--base", args.base, "--save-path", artifacts["data_coverage"]],
            expected_artifacts=[artifacts["data_coverage"]],
            skipped=args.skip_coverage,
        ),
        StepSpec(
            name="param_grid",
            script="kis_param_grid.py",
            args=[
                "--base", args.base,
                "--save-path", artifacts["param_grid"],
                "--workers", str(param_grid_workers),
                "--min-common-dates", str(args.min_common_dates),
            ],
            expected_artifacts=[artifacts["param_grid"]],
            skipped=args.skip_grid,
        ),
        StepSpec(
            name="walkforward",
            script="kis_walkforward.py",
            args=[
                "--base", args.base,
                "--save-path", artifacts["walkforward_results"],
                "--summary-path", artifacts["walkforward_summary"],
                "--train-years", str(args.train_years),
                "--test-years", str(args.test_years),
                "--step-years", str(args.step_years),
                "--min-common-dates", str(args.min_common_dates),
                "--min-oos-windows", str(args.min_oos_windows),
            ],
            expected_artifacts=[artifacts["walkforward_results"], artifacts["walkforward_summary"]],
            skipped=args.skip_walkforward,
        ),
        StepSpec(
            name="cost_sensitivity",
            script="kis_cost_sensitivity.py",
            args=[
                "--base", args.base,
                "--save-path", artifacts["cost_sensitivity"],
                "--roundtrip-costs", args.roundtrip_costs,
                "--min-common-dates", str(args.min_common_dates),
                "--top-n", str(args.top_n),
                "--regime-filter", str(args.regime_filter),
                "--stop-loss-pct", str(args.stop_loss_pct),
                "--trend-exit-ma", str(args.trend_exit_ma),
                "--regime-ma-window", str(args.regime_ma_window),
                "--regime-slope-window", str(args.regime_slope_window),
                "--regime-breadth-threshold", str(args.regime_breadth_threshold),
                "--vol-lookback", str(args.vol_lookback),
                "--target-vol-annual", str(args.target_vol_annual),
                "--max-weight", str(args.max_weight),
                "--min-gross-exposure", str(args.min_gross_exposure),
                "--score-top-k", str(args.score_top_k),
                "--score-power", str(args.score_power),
                "--regime-off-exposure", str(args.regime_off_exposure),
                "--allow-intraperiod-reentry", str(args.allow_intraperiod_reentry),
                "--reentry-cooldown-days", str(args.reentry_cooldown_days),
                "--osc-lookback", str(args.osc_lookback),
                "--osc-z-entry", str(args.osc_z_entry),
                "--osc-z-exit", str(args.osc_z_exit),
                "--osc-z-stop", str(args.osc_z_stop),
                "--osc-band-sigma", str(args.osc_band_sigma),
                "--osc-band-break-sigma", str(args.osc_band_break_sigma),
                "--osc-reentry-cooldown-days", str(args.osc_reentry_cooldown_days),
                "--rotation-top-k", str(args.rotation_top_k),
                "--rotation-tilt-strength", str(args.rotation_tilt_strength),
                "--rotation-min-sleeve-weight", str(args.rotation_min_sleeve_weight),
                "--range-slope-threshold", str(args.range_slope_threshold),
                "--range-dist-threshold", str(args.range_dist_threshold),
                "--range-breakout-persistence-threshold", str(args.range_breakout_persistence_threshold),
                "--range-breadth-tolerance", str(args.range_breadth_tolerance),
            ],
            expected_artifacts=[artifacts["cost_sensitivity"]],
            skipped=args.skip_cost,
        ),
        StepSpec(
            name="leaderboard",
            script="kis_research_summary.py",
            args=[
                "--base-summary-path", artifacts["baseline_summary"],
                "--grid-path", artifacts["param_grid"],
                "--walkforward-results-path", artifacts["walkforward_results"],
                "--walkforward-summary-path", artifacts["walkforward_summary"],
                "--cost-path", artifacts["cost_sensitivity"],
                "--save-path", artifacts["leaderboard"],
                "--grid-top-k", "5",
                "--operational-only", "0",
            ],
            expected_artifacts=[artifacts["leaderboard"]],
            skipped=args.skip_leaderboard,
        ),
        StepSpec(
            name="cost_stress_report",
            script="kis_cost_stress_report.py",
            args=[
                "--cost-path", artifacts["cost_sensitivity"],
                "--leaderboard-path", artifacts["leaderboard"],
                "--save-path", artifacts["cost_stress_report"],
            ],
            expected_artifacts=[artifacts["cost_stress_report"]],
            skipped=args.skip_cost_stress_report,
        ),
        StepSpec(
            name="sleeve_attribution_report",
            script="kis_sleeve_attribution_report.py",
            args=[
                "--base-summary-path", artifacts["baseline_summary"],
                "--leaderboard-path", artifacts["leaderboard"],
                "--save-path", artifacts["sleeve_attribution_report"],
            ],
            expected_artifacts=[artifacts["sleeve_attribution_report"]],
            skipped=args.skip_sleeve_report,
        ),
        StepSpec(
            name="sleeve_compare_report",
            script="kis_sleeve_compare.py",
            args=[
                "--base", args.base,
                "--save-path", artifacts["sleeve_compare_report"],
                "--min-common-dates", str(args.min_common_dates),
                "--top-n", str(args.top_n),
                "--fee-bps", str(args.fee_bps),
                "--regime-filter", str(args.regime_filter),
                "--stop-loss-pct", str(args.stop_loss_pct),
                "--trend-exit-ma", str(args.trend_exit_ma),
                "--regime-ma-window", str(args.regime_ma_window),
                "--regime-slope-window", str(args.regime_slope_window),
                "--regime-breadth-threshold", str(args.regime_breadth_threshold),
                "--vol-lookback", str(args.vol_lookback),
                "--target-vol-annual", str(args.target_vol_annual),
                "--max-weight", str(args.max_weight),
                "--min-gross-exposure", str(args.min_gross_exposure),
                "--score-top-k", str(args.score_top_k),
                "--score-power", str(args.score_power),
                "--regime-off-exposure", str(args.regime_off_exposure),
                "--allow-intraperiod-reentry", str(args.allow_intraperiod_reentry),
                "--reentry-cooldown-days", str(args.reentry_cooldown_days),
                "--osc-lookback", str(args.osc_lookback),
                "--osc-z-entry", str(args.osc_z_entry),
                "--osc-z-exit", str(args.osc_z_exit),
                "--osc-z-stop", str(args.osc_z_stop),
                "--osc-band-sigma", str(args.osc_band_sigma),
                "--osc-band-break-sigma", str(args.osc_band_break_sigma),
                "--osc-reentry-cooldown-days", str(args.osc_reentry_cooldown_days),
                "--rotation-top-k", str(args.rotation_top_k),
                "--rotation-tilt-strength", str(args.rotation_tilt_strength),
                "--rotation-min-sleeve-weight", str(args.rotation_min_sleeve_weight),
                "--range-slope-threshold", str(args.range_slope_threshold),
                "--range-dist-threshold", str(args.range_dist_threshold),
                "--range-breakout-persistence-threshold", str(args.range_breakout_persistence_threshold),
                "--range-breadth-tolerance", str(args.range_breadth_tolerance),
            ],
            expected_artifacts=[artifacts["sleeve_compare_report"]],
            skipped=args.skip_sleeve_compare,
        ),
        StepSpec(
            name="live_readiness",
            script="kis_live_readiness.py",
            args=[
                "--base-summary-path", artifacts["baseline_summary"],
                "--grid-path", artifacts["param_grid"],
                "--walkforward-summary-path", artifacts["walkforward_summary"],
                "--cost-path", artifacts["cost_sensitivity"],
                "--leaderboard-path", artifacts["leaderboard"],
                "--manifest-path", artifacts["run_manifest"],
                "--save-path", artifacts["live_readiness"],
                "--operational-only", "1",
            ],
            expected_artifacts=[artifacts["live_readiness"]],
            skipped=args.skip_live_readiness,
        ),
        StepSpec(
            name="shadow_portfolio",
            script="kis_shadow_portfolio.py",
            args=[
                "--base", args.base,
                "--live-readiness-path", artifacts["live_readiness"],
                "--manifest-path", artifacts["run_manifest"],
                "--strategy-name", args.strategy_name,
                "--save-path", artifacts["shadow_portfolio"],
                "--min-common-dates", str(args.min_common_dates),
            ],
            expected_artifacts=[artifacts["shadow_portfolio"]],
            skipped=args.skip_shadow_portfolio,
        ),
        StepSpec(
            name="shadow_rebalance_diff",
            script="kis_shadow_rebalance_diff.py",
            args=[
                "--base", args.base,
                "--live-readiness-path", artifacts["live_readiness"],
                "--manifest-path", artifacts["run_manifest"],
                "--current-portfolio-path", artifacts["shadow_portfolio"],
                "--previous-portfolio-path", previous_shadow_portfolio_path or "",
                "--save-path", artifacts["shadow_rebalance_diff"],
                "--strategy-name", args.strategy_name,
                "--min-common-dates", str(args.min_common_dates),
            ],
            expected_artifacts=[artifacts["shadow_rebalance_diff"]],
            skipped=args.skip_shadow_diff,
        ),
        StepSpec(
            name="shadow_performance",
            script="kis_shadow_performance.py",
            args=[
                "--base", args.base,
                "--live-readiness-path", artifacts["live_readiness"],
                "--manifest-path", artifacts["run_manifest"],
                "--current-portfolio-path", artifacts["shadow_portfolio"],
                "--previous-portfolio-path", previous_shadow_portfolio_path or "",
                "--diff-path", artifacts["shadow_rebalance_diff"],
                "--ledger-path", artifacts["shadow_ledger"],
                "--nav-path", artifacts["shadow_nav"],
                "--strategy-name", args.strategy_name,
                "--min-common-dates", str(args.min_common_dates),
                "--starting-capital", str(args.shadow_starting_capital),
                "--one-way-fee-bps", str(args.shadow_one_way_fee_bps),
                "--one-way-slippage-bps", str(args.shadow_one_way_slippage_bps),
            ],
            expected_artifacts=[artifacts["shadow_ledger"], artifacts["shadow_nav"]],
            skipped=args.skip_shadow_performance,
        ),
        StepSpec(
            name="shadow_health",
            script="kis_shadow_health.py",
            args=[
                "--live-readiness-path", artifacts["live_readiness"],
                "--manifest-path", artifacts["run_manifest"],
                "--portfolio-path", artifacts["shadow_portfolio"],
                "--diff-path", artifacts["shadow_rebalance_diff"],
                "--save-path", artifacts["shadow_health"],
                "--strategy-name", args.strategy_name,
                "--material-change-threshold", str(args.shadow_material_change_threshold),
            ],
            expected_artifacts=[artifacts["shadow_health"]],
            skipped=args.skip_shadow_health,
        ),
        StepSpec(
            name="shadow_ops_summary",
            script="kis_shadow_ops_summary.py",
            args=[
                "--live-readiness-path", artifacts["live_readiness"],
                "--manifest-path", artifacts["run_manifest"],
                "--health-path", artifacts["shadow_health"],
                "--diff-path", artifacts["shadow_rebalance_diff"],
                "--portfolio-path", artifacts["shadow_portfolio"],
                "--nav-path", artifacts["shadow_nav"],
                "--save-path", artifacts["shadow_ops_summary"],
                "--strategy-name", args.strategy_name,
            ],
            expected_artifacts=[artifacts["shadow_ops_summary"]],
            skipped=args.skip_shadow_ops_summary,
        ),
        StepSpec(
            name="shadow_exceptions",
            script="kis_shadow_exceptions.py",
            args=[
                "--live-readiness-path", artifacts["live_readiness"],
                "--manifest-path", artifacts["run_manifest"],
                "--health-path", artifacts["shadow_health"],
                "--ops-summary-path", artifacts["shadow_ops_summary"],
                "--portfolio-path", artifacts["shadow_portfolio"],
                "--nav-path", artifacts["shadow_nav"],
                "--save-path", artifacts["shadow_exceptions"],
                "--strategy-name", args.strategy_name,
            ],
            expected_artifacts=[artifacts["shadow_exceptions"]],
            skipped=args.skip_shadow_exceptions,
        ),
    ]


def run_step(step: StepSpec) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(ROOT / step.script), *step.args]
    ensure_step_output_dirs(step)
    print(f"\n=== {step.name} ===")
    print("command:", subprocess.list2cmdline(cmd))
    return subprocess.run(cmd, cwd=ROOT, text=True, check=False)


def main() -> int:
    args = parse_args()
    artifacts = contract.canonical_artifact_paths(args.output_base)
    started_at = datetime.now(timezone.utc)
    started_perf = perf_counter()
    run_id = build_run_id(started_at)
    manifest: dict[str, Any] = {
        "run_id": run_id,
        "run_timestamp_utc": started_at.isoformat(),
        "base_input_path": args.base,
        "output_base_path": args.output_base,
        "commands_executed": [],
        "produced_artifacts": [],
        "steps": [],
        "started_at": started_at.isoformat(),
        "finished_at": None,
        "duration_seconds": None,
        "final_status": "running",
        "failed_step": None,
    }

    previous_shadow_portfolio_path = copy_to_local_if_exists(
        artifacts["shadow_portfolio"], str(ROOT / ".shadow_previous_portfolio.csv")
    )
    steps = build_steps(args, previous_shadow_portfolio_path=previous_shadow_portfolio_path)
    manifest_path = artifacts["run_manifest"]
    final_status = "failed"
    failed_step: str | None = None
    write_json_any(manifest, manifest_path)

    try:
        for step in steps:
            cmd = [sys.executable, str(ROOT / step.script), *step.args]
            step_record: dict[str, Any] = {
                "name": step.name,
                "script": step.script,
                "command": cmd,
                "status": "skipped" if step.skipped else "pending",
                "expected_artifacts": step.expected_artifacts,
            }
            manifest["commands_executed"].append(cmd)

            if step.skipped:
                manifest["steps"].append(step_record)
                write_json_any(manifest, manifest_path)
                continue

            result = run_step(step)
            step_record["returncode"] = result.returncode
            if result.returncode != 0:
                step_record["status"] = "failed"
                manifest["steps"].append(step_record)
                failed_step = step.name
                finalize_manifest(manifest, manifest_path, started_at, started_perf, "failed", failed_step)
                print(f"step failed: {step.name} (returncode={result.returncode})")
                print(f"PIPELINE FAILED: {step.name}")
                return result.returncode

            missing = [path for path in step.expected_artifacts if not path_exists(path)]
            if missing:
                step_record["status"] = "failed_missing_artifacts"
                step_record["missing_artifacts"] = missing
                manifest["steps"].append(step_record)
                failed_step = step.name
                finalize_manifest(manifest, manifest_path, started_at, started_perf, "failed", failed_step)
                print(f"step failed: {step.name} missing artifacts")
                for path in missing:
                    print(f"  missing: {path}")
                print(f"PIPELINE FAILED: {step.name}")
                return 1

            step_record["status"] = "success"
            step_record["traceability_annotated_artifacts"] = annotate_step_artifacts(
                step, artifacts, run_id, started_at.isoformat()
            )
            step_record["produced_artifacts"] = step.expected_artifacts
            manifest["steps"].append(step_record)
            manifest["produced_artifacts"].extend(step.expected_artifacts)
            write_json_any(manifest, manifest_path)

        final_status = "success"
        failed_step = None
        finalize_manifest(manifest, manifest_path, started_at, started_perf, final_status, failed_step)
        print("\nProduced artifacts:")
        for path in sorted(set(manifest["produced_artifacts"] + [manifest_path])):
            print(path)
        print("PIPELINE SUCCESS")
        return 0
    finally:
        if manifest.get("final_status") == "running":
            finalize_manifest(manifest, manifest_path, started_at, started_perf, final_status, failed_step)


if __name__ == "__main__":
    raise SystemExit(main())
