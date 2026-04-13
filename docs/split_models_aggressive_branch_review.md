# Split Models Aggressive Branch Review

## Scope

- branch family: sector-constrained aggressive research variants
- retired comparison branch: `rule_sector_cap2_breadth_risk_off`
- surviving branch: `rule_sector_cap2_breadth_it_risk_off`

## Full-period comparison

- `rule_sector_cap2_breadth_risk_off`
  - CAGR: `36.40%`
  - MDD: `-32.23%`
  - Sharpe: `1.4960`
  - Annual turnover: `14.62`
- `rule_sector_cap2_breadth_it_risk_off`
  - CAGR: `36.90%`
  - MDD: `-32.23%`
  - Sharpe: `1.5201`
  - Annual turnover: `14.57`

## Delta review

- months compared: `61`
- positive months for `rule_sector_cap2_breadth_it_risk_off`: `2`
- negative months: `0`
- average monthly net-return delta: `+0.032%p`
- best delta month: `2020-02-28 -> 2020-03-31`, `+1.97%p`

## Interpretation

- the IT overlay does not improve the weak period in this branch family
- sector cap plus breadth risk-off already suppresses most IT concentration before the extra overlay can fire
- despite that, the IT-overlay version still dominates on full-period summary without introducing any negative month-level delta

## Verdict

- retire `rule_sector_cap2_breadth_risk_off` from active aggressive research focus
- keep `rule_sector_cap2_breadth_it_risk_off` as the single aggressive strong branch
- keep operational baseline separate as `rule_breadth_it_risk_off`
