# Split Models Shadow Runbook

## Current baseline

- promoted baseline variant: `rule_breadth_it_risk_off`
- baseline source: `split_models.backtest.BacktestConfig(baseline_variant="rule_breadth_it_risk_off")`
- shadow build entrypoint: `python .\build_split_models_shadow_report.py`
- research backtest entrypoint: `python .\run_split_models_backtest.py`

## Current reference metrics

- CAGR: `30.35%`
- MDD: `-26.36%`
- Sharpe: `1.4054`
- Annual turnover: `13.88`

Reference file:
- `output\split_models_shadow\split_models_backtest_summary.json`

## Daily shadow check

1. Run `python .\build_split_models_shadow_report.py`
2. Open `output\split_models_shadow\shadow_summary.json`
3. Confirm `baseline_variant` is `rule_breadth_it_risk_off`
4. Confirm `health_verdict` is `PASS`
5. Open `output\split_models_shadow\shadow_current_book.csv` and confirm the book was refreshed
6. Run `python .\check_split_models_shadow_drift.py` and confirm `drift_verdict=PASS`

## Main shadow artifacts

- `output\split_models_shadow\shadow_summary.json`
- `output\split_models_shadow\shadow_health.json`
- `output\split_models_shadow\shadow_current_book.csv`
- `output\split_models_shadow\shadow_turnover_monitor.csv`
- `output\split_models_shadow\shadow_monthly_sector_mix.csv`

## Escalation triggers

- `health_verdict` is not `PASS`
- current holdings drop below `4`
- current top1 weight exceeds `25%`
- current top3 weight exceeds `60%`
- recent average turnover exceeds `1.50`

## Notes

- `equal_weight_no_mad_min4` remains the key comparison baseline for research review.
- current operational shadow tracking is promoted to `rule_breadth_it_risk_off` because it improved drawdown and Sharpe further while leaving the latest current book unchanged.
