from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def _run_step(label: str, args: list[str]) -> None:
    print(f"[start] {label}")
    subprocess.run(args, cwd=ROOT, check=True)
    print(f"[done] {label}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--total-capital", type=float, default=None)
    parser.add_argument("--refresh-shadow", action="store_true")
    parser.add_argument("--refresh-reference", action="store_true")
    parser.add_argument("--status-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    python = sys.executable

    if args.status_only:
        status_args = [python, "build_split_models_shadow_status.py"]
        if args.json:
            status_args.append("--json")
        _run_step("show shadow status", status_args)
        return

    if args.refresh_shadow:
        _run_step("build shadow report", [python, "build_split_models_shadow_report.py"])

    _run_step(
        "build canonical transition",
        [python, "analyze_split_models_live_transition.py", "--canonical-shadow"],
    )

    rebalance_args = [python, "build_split_models_rebalance_orders.py"]
    if args.total_capital is not None:
        rebalance_args.extend(["--total-capital", str(args.total_capital)])
    _run_step("build rebalance orders", rebalance_args)

    if args.refresh_reference:
        _run_step(
            "refresh shadow drift reference",
            [python, "check_split_models_shadow_drift.py", "--refresh-reference"],
        )
    else:
        _run_step("check shadow drift", [python, "check_split_models_shadow_drift.py"])

    _run_step("build live readiness", [python, "build_split_models_live_readiness.py"])
    _run_step("build live packet", [python, "build_split_models_live_packet.py"])
    _run_step("archive operator handoff", [python, "archive_split_models_operator_handoff.py"])

    print("[summary] operator handoff artifacts refreshed")
    print(f"[summary] output_dir={ROOT / 'output' / 'split_models_shadow'}")


if __name__ == "__main__":
    main()
