# Split Models Aggressive Branch Review

## Scope

- branch family: sector-constrained aggressive research variants
- retired comparison branches: `rule_sector_cap2_breadth_risk_off`, `rule_sector_cap2_breadth_it_risk_off`, `rule_sector_cap2_breadth_it_us5_cap`
- surviving branch: `rule_sector_cap2_breadth_it_us5_top2_risk_on`

## Full-period comparison

- `rule_sector_cap2_breadth_it_us5_cap`
  - CAGR: `39.72%`
  - MDD: `-29.27%`
  - Sharpe: `1.5423`
  - Annual turnover: `14.57`
- `rule_sector_cap2_breadth_it_us5_risk_on`
  - CAGR: `42.80%`
  - MDD: `-29.27%`
  - Sharpe: `1.5776`
  - Annual turnover: `14.99`
- `rule_sector_cap2_breadth_it_us5_top2_risk_on`
  - CAGR: `47.05%`
  - MDD: `-29.27%`
  - Sharpe: `1.6165`
  - Annual turnover: `15.00`

## Delta review

- months compared: `61`
- positive months for `rule_sector_cap2_breadth_it_us5_top2_risk_on` vs `rule_sector_cap2_breadth_it_us5_risk_on`: `16`
- negative months: `7`
- average monthly net-return delta: `+0.338%p`
- best delta month: `2025-11-28 -> 2026-01-30`, `+5.75%p`
- worst delta month: `2023-07-31 -> 2023-08-31`, `-0.87%p`

## Weak-period review

- weak window: `2021-04-30 -> 2023-08-31`
- months compared: `25`
- baseline loss months: `11`
- loss months improved: `0`
- average monthly net-return delta: `+0.085%p`
- average loss-month delta: `-0.129%p`

## Concentration review

- months compared: `61`
- positive months: `16`
- negative months: `7`
- top 1 positive month share of total positive delta: `24.83%`
- top 3 positive month share: `46.06%`
- top 1 positive symbol share: `27.51%`
- top 3 positive symbol share: `74.91%`
- top symbols driving the edge: `PLTR`, `NVDA`, `MU`

## Concentration interpretation

- the month-level edge is not a single-month artifact, but it is still moderately concentrated in a handful of favorable months
- the symbol-level edge is much more concentrated than the month-level edge: most of the incremental alpha came from a small cluster of US information-technology winners
- that concentration is acceptable for an aggressive research branch, but it is a clear reason not to treat this as an operational baseline candidate

## Interpretation

- the top-slice risk-on overlay is a genuine new branch, not a cosmetic tweak: full-period CAGR and Sharpe both improved while MDD stayed flat
- month-level improvement is broad enough to avoid the prior "single-shock-month" failure mode
- the main caveats are weak-period quality and concentration: average weak-period return still improved slightly, but loss months were still a bit worse on average, and most of the incremental alpha came from a small set of US IT winners
- this remains a high-CAGR research branch, not an operational baseline candidate

## Verdict

- retire `rule_sector_cap2_breadth_risk_off`, `rule_sector_cap2_breadth_it_risk_off`, and `rule_sector_cap2_breadth_it_us5_cap` from active aggressive research focus
- keep `rule_sector_cap2_breadth_it_us5_top2_risk_on` as the single aggressive strong branch
- keep operational baseline separate as `rule_breadth_it_us5_cap`
