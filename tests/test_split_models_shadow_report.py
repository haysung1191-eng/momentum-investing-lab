from __future__ import annotations

from pathlib import Path

import build_split_models_shadow_report as shadow


def test_split_models_shadow_report_outputs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(shadow, "OUTPUT_DIR", tmp_path)
    shadow.main()

    expected = [
        "shadow_summary.csv",
        "shadow_summary.json",
        "shadow_health.csv",
        "shadow_health.json",
        "shadow_summary_history.csv",
        "shadow_health_history.csv",
        "shadow_turnover_monitor.csv",
        "shadow_current_book.csv",
    ]
    for name in expected:
        assert (tmp_path / name).exists()

    summary = (tmp_path / "shadow_summary.csv").read_text(encoding="utf-8-sig")
    assert "health_verdict" in summary
    health = (tmp_path / "shadow_health.csv").read_text(encoding="utf-8-sig")
    assert "Passed" in health

    shadow.main()
    history = (tmp_path / "shadow_summary_history.csv").read_text(encoding="utf-8-sig")
    assert "RunTimestamp" in history
