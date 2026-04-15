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
  - `benchmark_xs_mom_12_1_top5_eq`
  - `benchmark_xs_mom_12_1_us_stock_top5_eq`

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
- `benchmark_xs_mom_12_1_top5_eq`
  - CAGR: `49.10%`
  - MDD: `-32.83%`
  - Sharpe: `0.7958`
- `benchmark_xs_mom_12_1_us_stock_top5_eq`
  - CAGR: `33.12%`
  - MDD: `-26.74%`
  - Sharpe: `1.1441`

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
- versus `benchmark_xs_mom_12_1_top5_eq`
  - average monthly delta: `-2.99%p`
  - positive months: `34`
  - negative months: `27`
- versus `benchmark_xs_mom_12_1_us_stock_top5_eq`
  - average monthly delta: `-0.18%p`
  - positive months: `30`
  - negative months: `31`

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
- versus `benchmark_xs_mom_12_1_top5_eq`
  - average monthly delta: `-1.69%p`
  - positive months: `34`
  - negative months: `27`
- versus `benchmark_xs_mom_12_1_us_stock_top5_eq`
  - average monthly delta: `+1.11%p`
  - positive months: `33`
  - negative months: `28`

## Interpretation

- both current live baseline and current strongest aggressive branch still beat passive and simple timing benchmarks on both CAGR and Sharpe over the same `61`-month window
- the added `12-1` cross-sectional momentum benchmarks are the first genuinely hard external comparators
- `rule_breadth_it_us5_cap` does **not** beat the simple full-universe top-5 momentum benchmark on CAGR, but it does beat it meaningfully on Sharpe (`1.4482` vs `0.7958`) and on drawdown (`-25.24%` vs `-32.83%`)
- `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on` beats the simple full-universe top-5 momentum benchmark on CAGR (`49.65%` vs `49.10%`) and Sharpe (`1.6612` vs `0.7958`) while also keeping drawdown tighter (`-29.27%` vs `-32.83%`)
- the aggressive strongest branch also beats the simpler US-stock-only top-5 momentum benchmark on CAGR, Sharpe, and average monthly delta
- this benchmark chapter is now materially stronger: the surviving models are no longer only beating passive baselines, they are also competing against simple literature-like momentum rules

## Verdict

- keep `rule_breadth_it_us5_cap` as the operational baseline
- keep `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on` as the strongest aggressive research branch
- treat benchmark superiority as supportive evidence, not final proof: the next research step should make the benchmark chapter more statistically defensible, not merely broader
