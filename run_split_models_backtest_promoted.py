from __future__ import annotations

from pathlib import Path

from split_models.backtest import BacktestConfig, run_backtests


def main() -> None:
    promoted_dir = Path("output") / "split_models_backtest_promoted"
    outputs = run_backtests(
        output_dir=promoted_dir,
        config=BacktestConfig(baseline_variant="rule_kr_unknown_off"),
    )
    summary = outputs["trading_book_backtest_summary"].iloc[0]
    print("baseline_variant=rule_kr_unknown_off")
    print(f"months={int(summary['Months'])}")
    print(f"cagr={summary['CAGR']:.4f}")
    print(f"mdd={summary['MDD']:.4f}")
    print(f"sharpe={summary['Sharpe']:.4f}")


if __name__ == "__main__":
    main()
