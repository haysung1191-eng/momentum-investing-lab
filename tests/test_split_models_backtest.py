from __future__ import annotations

from pathlib import Path

from split_models.backtest import BacktestConfig, run_backtests


def test_split_models_backtest_smoke(tmp_path: Path) -> None:
    outputs = run_backtests(output_dir=tmp_path, config=BacktestConfig(signal_start="2022-01-31"))

    assert "CAGR" in outputs["trading_book_backtest_summary"].columns
    assert "WatchGrade" in outputs["tenbagger_backtest_occurrences"].columns
    assert "Benchmark" in outputs["trading_book_benchmark_compare"].columns
    assert "WindowStart" in outputs["trading_book_walkforward_summary"].columns
    assert "OneWayCostBps" in outputs["trading_book_cost_sensitivity"].columns
    assert "Variant" in outputs["trading_book_ablation_compare"].columns
    assert "Variant" in outputs["trading_book_refinement_compare"].columns
    assert "Contribution" in outputs["trading_book_market_contribution_summary"].columns
    assert "WindowStart" in outputs["trading_book_weak_period_window"].columns
    assert (tmp_path / "trading_book_backtest_nav.csv").exists()
    assert (tmp_path / "trading_book_backtest_summary.csv").exists()
    assert (tmp_path / "trading_book_benchmark_compare.csv").exists()
    assert (tmp_path / "trading_book_walkforward_summary.csv").exists()
    assert (tmp_path / "trading_book_cost_sensitivity.csv").exists()
    assert (tmp_path / "trading_book_ablation_compare.csv").exists()
    assert (tmp_path / "trading_book_refinement_compare.csv").exists()
    assert (tmp_path / "trading_book_market_contribution_summary.csv").exists()
    assert (tmp_path / "trading_book_sector_contribution_summary.csv").exists()
    assert (tmp_path / "trading_book_symbol_contribution_summary.csv").exists()
    assert (tmp_path / "trading_book_weak_period_window.csv").exists()
    assert (tmp_path / "trading_book_weak_period_monthly_diagnostics.csv").exists()
    assert (tmp_path / "trading_book_weak_period_market_summary.csv").exists()
    assert (tmp_path / "trading_book_weak_period_sector_summary.csv").exists()
    assert (tmp_path / "tenbagger_backtest_occurrences.csv").exists()
    assert (tmp_path / "tenbagger_backtest_grade_summary.csv").exists()


def test_split_models_backtest_promoted_variant(tmp_path: Path) -> None:
    outputs = run_backtests(
        output_dir=tmp_path,
        config=BacktestConfig(signal_start="2022-01-31", baseline_variant="equal_weight_no_mad"),
    )

    summary = outputs["trading_book_backtest_summary"].iloc[0]
    assert float(summary["CAGR"]) == float(summary["CAGR"])
    assert (tmp_path / "split_models_backtest_summary.json").exists()
