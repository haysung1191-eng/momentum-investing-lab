# Split Models Quality vs Headline Review

## Scope

- compare the current strongest against two different near-miss directions
- strongest:
  - `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
- quality near-miss:
  - `bonus_recipient_top1_third_85_15`
- skip-entry near-miss:
  - `tail_skip_entry_flowweakest_new_bottom4_top25_mid75`
- risk-off-strength near-miss:
  - `risk_off_strength_breadth080`

## Result

- headline leader: `bonus_recipient_top1_third_85_15`
- quality leader: `bonus_recipient_top1_third_85_15`
- lowest turnover variant: `tail_skip_entry_flowweakest_new_bottom4_top25_mid75`

## Quality Near-Miss

- CAGR: `65.43%`
- MDD: `-29.52%`
- Sharpe: `1.6927`
- Annual turnover: `15.81`
- `75 bps` cost CAGR delta vs strongest: `1.68%p`
- walk-forward: `3 positive / 1 negative`
- top 3 positive symbol share: `49.58%`

## Skip-Entry Near-Miss

- CAGR: `63.21%`
- MDD: `-28.77%`
- Sharpe: `1.6625`
- Annual turnover: `14.73`
- `75 bps` cost CAGR delta vs strongest: `0.53%p`
- walk-forward: `3 positive / 1 negative`
- top 3 positive symbol share: `49.04%`

## Risk-Off-Strength Near-Miss

- CAGR: `63.50%`
- MDD: `-29.95%`
- Sharpe: `1.6847`
- Annual turnover: `15.57`
- `75 bps` cost CAGR delta vs strongest: `0.12%p`
- walk-forward: `3 positive / 1 negative`
- top 3 positive symbol share: `46.55%`

## Interpretation

- `bonus_recipient_top1_third_85_15` is the best blended quality extension
  - CAGR improves even more
  - walk-forward stays at `3-1` and cost stays positive
  - but drawdown is slightly worse and turnover still rises
- `tail_skip_entry_flowweakest_new_bottom4_top25_mid75` is the best headline extension
  - CAGR and turnover improve together
  - but Sharpe still stays materially below the strongest
- `risk_off_strength_breadth080` is the closest defensive headline-ish extension
  - CAGR is slightly above the strongest
  - but drawdown gets worse and Sharpe still slips
- the strongest remains the only branch that stays balanced enough across headline, quality, and promotion robustness

## Verdict

- keep the current strongest as the single aggressive mainline branch
- treat the quality near-miss as the best quality-tilted alternative
- treat the skip-entry near-miss as the best headline-tilted alternative
- treat the risk-off-strength near-miss as a defensive headline-ish alternative, not a promotion
- do not promote either near-miss without solving their remaining quality gap
