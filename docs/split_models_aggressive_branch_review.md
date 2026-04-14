# Split Models Aggressive Branch Review

## Scope

- branch family: sector-constrained aggressive research variants
- retired comparison branches: `rule_sector_cap2_breadth_risk_off`, `rule_sector_cap2_breadth_it_risk_off`, `rule_sector_cap2_breadth_it_us5_cap`
- surviving branch: `rule_sector_cap2_breadth_it_us5_risk_on`

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

## Delta review

- months compared: `61`
- positive months for `rule_sector_cap2_breadth_it_us5_risk_on` vs `rule_sector_cap2_breadth_it_us5_cap`: `15`
- negative months: `10`
- average monthly net-return delta: `+0.250%p`
- best delta month: `2025-11-28 -> 2026-01-30`, `+3.64%p`
- worst delta month: `2023-08-31 -> 2023-10-31`, `-1.15%p`

## Weak-period review

- weak window: `2021-04-30 -> 2023-08-31`
- months compared: `25`
- baseline loss months: `11`
- loss months improved: `0`
- average monthly net-return delta: `+0.074%p`
- average loss-month delta: `-0.154%p`

## Interpretation

- the risk-on overlay is a genuine new branch, not a cosmetic tweak: full-period CAGR and Sharpe both improved while MDD stayed flat
- month-level improvement is broad enough to avoid the prior "single-shock-month" failure mode
- the main caveat is weak-period quality: average weak-period return still improved slightly, but loss months became a bit worse on average
- this remains a high-CAGR research branch, not an operational baseline candidate

## Verdict

- retire `rule_sector_cap2_breadth_risk_off`, `rule_sector_cap2_breadth_it_risk_off`, and `rule_sector_cap2_breadth_it_us5_cap` from active aggressive research focus
- keep `rule_sector_cap2_breadth_it_us5_risk_on` as the single aggressive strong branch
- keep operational baseline separate as `rule_breadth_it_us5_cap`
