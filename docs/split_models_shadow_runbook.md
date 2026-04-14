# Split Models Shadow Runbook

## Current baseline

- promoted baseline variant: `rule_breadth_it_us5_cap`
- baseline source: `split_models.backtest.BacktestConfig(baseline_variant="rule_breadth_it_us5_cap")`
- shadow build entrypoint: `python .\build_split_models_shadow_report.py`
- research backtest entrypoint: `python .\run_split_models_backtest.py`

## Current reference metrics

- CAGR: `33.43%`
- MDD: `-25.24%`
- Sharpe: `1.4482`
- Annual turnover: `13.72`

Reference file:
- `output\split_models_shadow\split_models_backtest_summary.json`

## Daily shadow check

1. Run `python .\build_split_models_shadow_report.py`
2. Open `output\split_models_shadow\shadow_summary.json`
3. Confirm `baseline_variant` is `rule_breadth_it_us5_cap`
4. Confirm `health_verdict` is `PASS`
5. Open `output\split_models_shadow\shadow_current_book.csv` and confirm the book was refreshed
6. Run `python .\check_split_models_shadow_drift.py` and confirm `drift_verdict=PASS`
7. Run `python .\analyze_split_models_live_transition.py --canonical-shadow` and inspect the transition diff before any live rebalance
8. Run `python .\build_split_models_rebalance_orders.py` and inspect the order sheet before sending any orders
9. Open the market summary and execution summary to separate KR and US execution windows before placing orders
10. Run `python .\build_split_models_live_readiness.py` and require `live_readiness_verdict=GO` before any live transition
11. Run `python .\build_split_models_live_packet.py` and use the packet as the single-file operator handoff before placing orders

## Main shadow artifacts

- `output\split_models_shadow\shadow_summary.json`
- `output\split_models_shadow\shadow_health.json`
- `output\split_models_shadow\shadow_current_book.csv`
- `output\split_models_shadow\shadow_live_transition_summary.json`
- `output\split_models_shadow\shadow_live_transition_diff.csv`
- `output\split_models_shadow\shadow_rebalance_orders.csv`
- `output\split_models_shadow\shadow_rebalance_market_summary.csv`
- `output\split_models_shadow\shadow_rebalance_execution_summary.json`
- `output\split_models_shadow\shadow_live_readiness.json`
- `output\split_models_shadow\shadow_live_transition_packet.md`
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
- current operational shadow tracking is promoted to `rule_breadth_it_us5_cap` because it reduced US concentration while improving CAGR, MDD, Sharpe, and turnover versus the prior shadow candidate.
- `build_split_models_rebalance_orders.py --total-capital <account_value>` can be used to attach rough notional targets to the canonical transition diff.
