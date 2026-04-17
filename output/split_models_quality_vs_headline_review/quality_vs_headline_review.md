# Split Models Quality vs Headline Review

## Scope

- compare the current strongest against two different near-miss directions
- strongest:
  - `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
- quality near-miss:
  - `bonus_recipient_top1_third_67_33`
- skip-entry near-miss:
  - `tail_skip_entry_flowweakest_new_bottom4_top50_mid50`

## Result

- headline leader: `tail_skip_entry_flowweakest_new_bottom4_top50_mid50`
- quality leader: `bonus_recipient_top1_third_67_33`
- lowest turnover variant: `tail_skip_entry_flowweakest_new_bottom4_top50_mid50`

## Quality Near-Miss

- CAGR: `63.21%`
- MDD: `-29.09%`
- Sharpe: `1.7018`
- Annual turnover: `15.94`
- `75 bps` cost CAGR delta vs strongest: `-0.46%p`
- walk-forward: `2 positive / 2 negative`
- top 3 positive symbol share: `35.09%`

## Skip-Entry Near-Miss

- CAGR: `63.75%`
- MDD: `-29.23%`
- Sharpe: `1.6636`
- Annual turnover: `14.72`
- `75 bps` cost CAGR delta vs strongest: `1.04%p`
- walk-forward: `3 positive / 1 negative`
- top 3 positive symbol share: `48.02%`

## Interpretation

- `bonus_recipient_top1_third_67_33` is the best quality extension
  - Sharpe and MDD improve the most
  - but turnover jumps and cost-adjusted CAGR turns negative
- `tail_skip_entry_flowweakest_new_bottom4_top50_mid50` is the best headline extension
  - CAGR and turnover improve together
  - but Sharpe still stays materially below the strongest
- the strongest remains the only branch that stays balanced enough across headline, quality, and promotion robustness

## Verdict

- keep the current strongest as the single aggressive mainline branch
- treat the quality near-miss as the best quality-tilted alternative
- treat the skip-entry near-miss as the best headline-tilted alternative
- do not promote either near-miss without solving their remaining quality gap
