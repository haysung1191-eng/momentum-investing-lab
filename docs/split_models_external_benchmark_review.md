# Split Models External Benchmark Review

## Scope

- compare the current operational baseline and strongest aggressive research branch against simple external equity/ETF benchmarks
- model variants:
  - `rule_breadth_it_us5_cap`
  - `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on`
- benchmark set:
  - `benchmark_spy_buy_hold`
  - `benchmark_kospi200_buy_hold`
  - `benchmark_spy_kospi_equal_weight`
  - `benchmark_spy_sma10`

## Why this review exists

- internal branch comparisons alone are not enough for research defense
- this review asks whether the live baseline and strongest aggressive branch beat simple, recognizable external standards

## Benchmark metrics

- `benchmark_spy_buy_hold`
  - CAGR: `15.10%`
  - MDD: `-21.05%`
  - Sharpe: `0.9921`
- `benchmark_kospi200_buy_hold`
  - CAGR: `21.76%`
  - MDD: `-35.58%`
  - Sharpe: `0.9253`
- `benchmark_spy_kospi_equal_weight`
  - CAGR: `19.08%`
  - MDD: `-26.16%`
  - Sharpe: `1.0971`
- `benchmark_spy_sma10`
  - CAGR: `11.01%`
  - MDD: `-15.36%`
  - Sharpe: `1.0227`

## Model metrics

- `rule_breadth_it_us5_cap`
  - CAGR: `33.43%`
  - MDD: `-25.24%`
  - Sharpe: `1.4482`
- `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on`
  - CAGR: `49.65%`
  - MDD: `-29.27%`
  - Sharpe: `1.6612`

## Relative comparison

### Operational baseline: `rule_breadth_it_us5_cap`

- versus `benchmark_spy_buy_hold`
  - average monthly delta: `+1.62%p`
  - positive months: `35`
  - negative months: `26`
- versus `benchmark_kospi200_buy_hold`
  - average monthly delta: `+0.86%p`
  - positive months: `35`
  - negative months: `26`
- versus `benchmark_spy_kospi_equal_weight`
  - average monthly delta: `+1.24%p`
  - positive months: `33`
  - negative months: `28`
- versus `benchmark_spy_sma10`
  - average monthly delta: `+2.05%p`
  - positive months: `35`
  - negative months: `26`

### Aggressive strongest branch: `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on`

- versus `benchmark_spy_buy_hold`
  - average monthly delta: `+2.91%p`
  - positive months: `35`
  - negative months: `26`
- versus `benchmark_kospi200_buy_hold`
  - average monthly delta: `+2.16%p`
  - positive months: `33`
  - negative months: `28`
- versus `benchmark_spy_kospi_equal_weight`
  - average monthly delta: `+2.54%p`
  - positive months: `36`
  - negative months: `25`
- versus `benchmark_spy_sma10`
  - average monthly delta: `+3.34%p`
  - positive months: `37`
  - negative months: `24`

## Interpretation

- both current live baseline and current strongest aggressive branch beat all four simple external benchmarks on CAGR and Sharpe over the same `61`-month window
- the operational baseline is not just an internally optimized model; it also clears diversified passive and simple trend-following benchmarks by a meaningful margin
- the aggressive branch remains far ahead on headline performance, but that does not cancel the concentration warnings already documented elsewhere
- this review improves external validity, but it is still a first benchmark layer rather than a full academic benchmark chapter

## Verdict

- keep `rule_breadth_it_us5_cap` as the operational baseline
- keep `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on` as the strongest aggressive research branch
- treat benchmark superiority as supportive evidence, not final proof: the next research step should expand this benchmark chapter beyond passive and simple timing rules
