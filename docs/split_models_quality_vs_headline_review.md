# Split Models Quality vs Headline Review

## Scope

- compare the current strongest against two different near-miss directions
- strongest:
  - `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
- quality near-miss:
  - `bonus_recipient_top1_third_75_25`
- skip-entry near-miss:
  - `tail_skip_entry_flowweakest_new_bottom4_top25_mid75`

## Why this review exists

- recent near-miss work split into two different directions:
  - one branch improves quality
  - another branch improves headline CAGR and turnover
- this review freezes that split so the project does not keep mixing up `higher quality` with `better strongest`

## Current reading

- `bonus_recipient_top1_third_75_25` is the best blended quality extension
  - CAGR and Sharpe both improve
  - concentration stays much lower than the strongest
  - but walk-forward stays mixed and turnover still rises
- `tail_skip_entry_flowweakest_new_bottom4_top25_mid75` is the best headline extension
  - CAGR stays at strongest level
  - drawdown and turnover improve
  - but Sharpe remains clearly below the strongest
- the current strongest still matters because it stays the most balanced point across:
  - headline CAGR
  - quality
  - promotion robustness

## Verdict

- keep the current strongest as the mainline aggressive branch
- treat the quality near-miss as the best quality-tilted alternative
- treat the skip-entry near-miss as the best headline-tilted alternative
- do not promote either near-miss yet
