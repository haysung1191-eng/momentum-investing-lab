from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

import archive_split_models_operator_handoff as archive_tools
import build_split_models_live_packet as live_packet
import build_split_models_live_readiness as live_readiness
import build_split_models_rebalance_orders as rebalance_orders
import build_split_models_shadow_status as shadow_status
import run_split_models_operator_handoff as handoff_runner


def test_split_models_operator_tools_build_outputs(tmp_path: Path, monkeypatch, capsys) -> None:
    shadow_dir = tmp_path / "shadow"
    archive_dir = tmp_path / "archive"
    shadow_dir.mkdir(parents=True)
    archive_dir.mkdir(parents=True)

    _write_json(
        shadow_dir / "shadow_summary.json",
        {
            "baseline_variant": "rule_breadth_it_us5_cap",
            "health_verdict": "PASS",
            "recent_avg_turnover": 0.96,
            "current_holdings": 8,
            "current_top1_weight": 0.125,
            "current_top3_weight": 0.375,
            "current_dominant_sector": "Industrials",
        },
    )
    _write_json(shadow_dir / "shadow_drift_report.json", {"drift_verdict": "PASS"})
    _write_json(
        shadow_dir / "shadow_live_transition_summary.json",
        {
            "baseline_variant": "rule_breadth_it_risk_off",
            "candidate_variant": "rule_breadth_it_us5_cap",
            "signal_date": "2026-01-30",
            "weight_turnover": 0.11111111111111113,
        },
    )
    _write_csv(
        shadow_dir / "shadow_live_transition_diff.csv",
        [
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "GILD",
                "Name": "Gilead",
                "Sector": "Health Care",
                "BaselineWeight": 0.1111111111,
                "CandidateWeight": 0.0,
                "WeightDelta": -0.1111111111,
                "Action": "Sell",
            },
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "LMT",
                "Name": "Lockheed Martin",
                "Sector": "Industrials",
                "BaselineWeight": 0.1111111111,
                "CandidateWeight": 0.125,
                "WeightDelta": 0.0138888889,
                "Action": "Add",
            },
            {
                "Market": "KR",
                "AssetType": "ETF",
                "Symbol": "069500",
                "Name": "069500",
                "Sector": "ETF",
                "BaselineWeight": 0.1111111111,
                "CandidateWeight": 0.125,
                "WeightDelta": 0.0138888889,
                "Action": "Add",
            },
        ],
    )

    monkeypatch.setattr(rebalance_orders, "SHADOW_DIR", shadow_dir)
    monkeypatch.setattr(live_readiness, "SHADOW_DIR", shadow_dir)
    monkeypatch.setattr(live_packet, "SHADOW_DIR", shadow_dir)
    monkeypatch.setattr(shadow_status, "SHADOW_DIR", shadow_dir)
    monkeypatch.setattr(archive_tools, "SHADOW_DIR", shadow_dir)
    monkeypatch.setattr(archive_tools, "ARCHIVE_DIR", archive_dir)

    monkeypatch.setattr(sys, "argv", ["build_split_models_rebalance_orders.py", "--total-capital", "100000000"])
    rebalance_orders.main()

    execution_summary = _read_json(shadow_dir / "shadow_rebalance_execution_summary.json")
    assert execution_summary["sell_count"] == 1
    assert execution_summary["buy_count"] == 2
    assert execution_summary["actionable_rows"] == 3

    live_readiness.main()
    readiness = _read_json(shadow_dir / "shadow_live_readiness.json")
    assert readiness["live_readiness_verdict"] == "GO"
    assert readiness["checks_passed"] == readiness["checks_total"] == 7

    live_packet.main()
    packet = (shadow_dir / "shadow_live_transition_packet.md").read_text(encoding="utf-8")
    assert "Split Models Live Transition Packet" in packet
    assert "SELL `GILD`" in packet
    assert "BUY `LMT`" in packet

    class _FakeNow:
        @staticmethod
        def now() -> "_FakeTimestamp":
            return _FakeTimestamp()

    class _FakeTimestamp:
        @staticmethod
        def strftime(fmt: str) -> str:
            assert fmt == "%Y%m%dT%H%M%S"
            return "20260414T120000"

    monkeypatch.setattr(archive_tools, "datetime", _FakeNow)
    archive_tools.main()

    manifest = pd.read_csv(archive_dir / "archive_manifest.csv")
    assert manifest.iloc[0]["BaselineVariant"] == "rule_breadth_it_us5_cap"
    assert manifest.iloc[0]["LiveReadinessVerdict"] == "GO"
    archived_packet = archive_dir / "20260414T120000" / "shadow_live_transition_packet.md"
    assert archived_packet.exists()

    _write_json(
        shadow_dir / "split_models_backtest_summary.json",
        {
            "trading_book": {
                "CAGR": 0.3343,
                "MDD": -0.2524,
                "Sharpe": 1.4482,
            }
        },
    )
    shadow_status.main([])
    output = capsys.readouterr().out
    assert "baseline_variant=rule_breadth_it_us5_cap" in output
    assert "live_readiness=GO" in output
    assert "market_US_sell_orders=1" in output

    shadow_status.main(["--json"])
    json_output = capsys.readouterr().out
    payload = json.loads(json_output)
    assert payload["baseline_variant"] == "rule_breadth_it_us5_cap"
    assert payload["live_readiness"] == "GO"
    assert payload["market_US_sell_orders"] == 1


def test_split_models_operator_handoff_runner_invokes_steps_in_order(monkeypatch) -> None:
    calls: list[list[str]] = []

    def _fake_run(args: list[str], cwd: Path, check: bool) -> None:
        assert cwd == handoff_runner.ROOT
        assert check is True
        calls.append(args)

    monkeypatch.setattr(handoff_runner.subprocess, "run", _fake_run)
    monkeypatch.setattr(handoff_runner.sys, "executable", "python")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_split_models_operator_handoff.py",
            "--total-capital",
            "100000000",
            "--refresh-shadow",
            "--refresh-reference",
        ],
    )

    handoff_runner.main()

    assert calls == [
        ["python", "build_split_models_shadow_report.py"],
        ["python", "analyze_split_models_live_transition.py", "--canonical-shadow"],
        ["python", "build_split_models_rebalance_orders.py", "--total-capital", "100000000.0"],
        ["python", "check_split_models_shadow_drift.py", "--refresh-reference"],
        ["python", "build_split_models_live_readiness.py"],
        ["python", "build_split_models_live_packet.py"],
        ["python", "archive_split_models_operator_handoff.py"],
    ]


def test_split_models_operator_handoff_runner_status_only(monkeypatch) -> None:
    calls: list[list[str]] = []

    def _fake_run(args: list[str], cwd: Path, check: bool) -> None:
        assert cwd == handoff_runner.ROOT
        assert check is True
        calls.append(args)

    monkeypatch.setattr(handoff_runner.subprocess, "run", _fake_run)
    monkeypatch.setattr(handoff_runner.sys, "executable", "python")
    monkeypatch.setattr(sys, "argv", ["run_split_models_operator_handoff.py", "--status-only"])

    handoff_runner.main()

    assert calls == [["python", "build_split_models_shadow_status.py"]]


def test_split_models_operator_handoff_runner_status_only_json(monkeypatch) -> None:
    calls: list[list[str]] = []

    def _fake_run(args: list[str], cwd: Path, check: bool) -> None:
        assert cwd == handoff_runner.ROOT
        assert check is True
        calls.append(args)

    monkeypatch.setattr(handoff_runner.subprocess, "run", _fake_run)
    monkeypatch.setattr(handoff_runner.sys, "executable", "python")
    monkeypatch.setattr(sys, "argv", ["run_split_models_operator_handoff.py", "--status-only", "--json"])

    handoff_runner.main()

    assert calls == [["python", "build_split_models_shadow_status.py", "--json"]]


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_csv(path: Path, rows: list[dict]) -> None:
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")
