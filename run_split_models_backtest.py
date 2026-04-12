from __future__ import annotations

from split_models.backtest import BacktestConfig, run_backtests


def main() -> None:
    outputs = run_backtests(config=BacktestConfig(baseline_variant="equal_weight_no_mad"))
    summary = outputs["trading_book_backtest_summary"].iloc[0]
    print("baseline_variant=equal_weight_no_mad")
    print(f"months={int(summary['Months'])}")
    print(f"cagr={summary['CAGR']:.4f}")
    print(f"mdd={summary['MDD']:.4f}")
    print(f"sharpe={summary['Sharpe']:.4f}")
    print(f"tenbagger_occurrences={len(outputs['tenbagger_backtest_occurrences'])}")


if __name__ == "__main__":
    main()
