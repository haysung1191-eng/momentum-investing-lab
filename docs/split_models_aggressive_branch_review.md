# Split Models Aggressive Branch Review

## Scope

- branch family: sector-constrained aggressive research variants
- retired comparison branches: `rule_sector_cap2_breadth_risk_off`, `rule_sector_cap2_breadth_it_risk_off`
- surviving branch: `rule_sector_cap2_breadth_it_us5_cap`

## Full-period comparison

- `rule_sector_cap2_breadth_it_risk_off`
  - CAGR: `36.90%`
  - MDD: `-32.23%`
  - Sharpe: `1.5201`
  - Annual turnover: `14.57`
- `rule_sector_cap2_breadth_it_us5_cap`
  - CAGR: `39.72%`
  - MDD: `-29.27%`
  - Sharpe: `1.5423`
  - Annual turnover: `14.57`

## Delta review

- months compared: `61`
- positive months for `rule_sector_cap2_breadth_it_us5_cap` vs `rule_sector_cap2_breadth_it_risk_off`: `29`
- negative months: `18`
- average monthly net-return delta: `+0.236%p`
- best delta month: `2020-07-31 -> 2020-08-31`, `+4.12%p`
- worst delta month: `2020-08-31 -> 2020-10-30`, `-2.78%p`

## Weak-period review

- weak window: `2021-04-30 -> 2023-08-31`
- months compared: `25`
- baseline loss months: `10`
- loss months improved: `4`
- average monthly net-return delta: `+0.146%p`
- average loss-month delta: `+0.132%p`

## Interpretation

- the US-5 cap changes this branch family more materially than the prior IT overlay alone
- improvement is no longer concentrated in one or two shock months; month-level wins are broader and weak-period losses improve in aggregate
- this remains an aggressive research branch, but it is no longer a narrow-period cosmetic refinement

## Verdict

- retire `rule_sector_cap2_breadth_risk_off` and `rule_sector_cap2_breadth_it_risk_off` from active aggressive research focus
- keep `rule_sector_cap2_breadth_it_us5_cap` as the single aggressive strong branch
- keep operational baseline separate as `rule_breadth_it_us5_cap`
