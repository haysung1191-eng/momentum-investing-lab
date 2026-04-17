# Split Models Tradeoff Frontier Review

## Scope

- compare the current aggressive strongest branch against recent nearby challengers that trade headline strength for broader edge
- current strongest:
  - `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
- challenger set:
  - `hybrid_top2_plus_third00125`
  - `bonus_schedule_first55_second45`
  - `bonus_recipient_top1_third_85_15`
  - `tail_skip_entry_flowweakest_new_bottom4_top25_mid75`
  - `tail_release_to_nonbottom_proportional`
  - `top2_split_49_51`
  - `alt_family_top3_flat_bonus18`

## Why this review exists

- recent exploratory work kept finding the same pattern:
  - broader and less concentrated challengers are possible
  - but they struggle to keep strongest-level CAGR and promotion-grade robustness
- this review freezes that trade-off in one place so the project does not keep rediscovering the same near-miss pattern

## Result

- current strongest
  - CAGR: `63.16%`
  - MDD: `-29.27%`
  - Sharpe: `1.6892`
  - Annual turnover: `15.32`
- `hybrid_top2_plus_third00125`
  - CAGR: `63.12%`
  - MDD: `-29.27%`
  - Sharpe: `1.6895`
  - Annual turnover: `15.32`
  - walk-forward: `2` positive CAGR windows, `2` negative
  - `75 bps` CAGR delta vs strongest: `-0.04%p`
  - top 3 positive symbol share: `39.00%`
- `bonus_schedule_first55_second45`
  - CAGR: `63.58%`
  - MDD: `-29.33%`
  - Sharpe: `1.6902`
  - Annual turnover: `15.34`
  - walk-forward: `2` positive CAGR windows, `2` negative
  - `75 bps` CAGR delta vs strongest: `+0.37%p`
  - top 3 positive symbol share: `57.68%`
- `bonus_recipient_top1_third_85_15`
  - CAGR: `65.43%`
  - MDD: `-29.52%`
  - Sharpe: `1.6927`
  - Annual turnover: `15.81`
  - walk-forward: `3` positive CAGR windows, `1` negative
  - `75 bps` CAGR delta vs strongest: `+1.68%p`
  - top 3 positive symbol share: `49.58%`
- `tail_skip_entry_flowweakest_new_bottom4_top25_mid75`
  - CAGR: `63.21%`
  - MDD: `-28.77%`
  - Sharpe: `1.6625`
  - Annual turnover: `14.73`
  - walk-forward: `3` positive CAGR windows, `1` negative
  - `75 bps` CAGR delta vs strongest: `+0.53%p`
  - top 3 positive symbol share: `49.04%`
- `tail_release_to_nonbottom_proportional`
  - CAGR: `70.94%`
  - MDD: `-37.73%`
  - Sharpe: `1.5096`
  - Annual turnover: `15.50`
  - walk-forward: `3` positive CAGR windows, `1` negative
  - `75 bps` CAGR delta vs strongest: `+7.00%p`
  - top 3 positive symbol share: `39.20%`
- `top2_split_49_51`
  - CAGR: `62.84%`
  - MDD: `-29.25%`
  - Sharpe: `1.6888`
  - Annual turnover: `15.35`
  - walk-forward: `1` positive CAGR window, `3` negative
  - `75 bps` CAGR delta vs strongest: `-0.32%p`
  - top 3 positive symbol share: `45.59%`
- `alt_family_top3_flat_bonus18`
  - CAGR: `46.12%`
  - MDD: `-29.27%`
  - Sharpe: `1.6105`
  - Annual turnover: `15.14`
  - walk-forward: `0` positive CAGR windows, `3` negative
  - `75 bps` CAGR delta vs strongest: `-15.66%p`
  - top 3 positive symbol share: `29.14%`

## Interpretation

- the current strongest is still the clear `promotion-grade stronger` point on the frontier
  - it is no longer the best raw-CAGR point once the `55/45` bonus near-miss is included
  - but it is still the strongest candidate that clears the broader promotion-defense stack
- `hybrid_top2_plus_third00125` is the best `broader` near-miss
  - Sharpe is still slightly better than the strongest
  - drawdown is effectively tied to slightly better than the strongest
  - concentration is much lower than the strongest
  - CAGR loss is now only `0.04%p`, but the walk-forward result still degrades to `2-2`
- `bonus_schedule_first55_second45` is the best `stronger-like` near-miss
  - full-period CAGR, Sharpe, and `75 bps` cost all improve versus the strongest
  - but walk-forward still stays `2-2`
  - drawdown also gets slightly worse, so it does not clear the promotion stack
- `bonus_recipient_top1_third_85_15` is the best `blended quality` near-miss
  - CAGR improves the most among the quality-family challengers
  - walk-forward stays at `3-1` and cost remains positive
  - but drawdown is slightly worse and turnover remains higher, so it still misses promotion grade
- `tail_skip_entry_flowweakest_new_bottom4_top25_mid75` is the best `skip-entry stronger-like` near-miss
  - CAGR, drawdown, and turnover all improve versus the strongest
  - walk-forward also stays mostly positive at `3-1`
  - but Sharpe remains meaningfully lower than the strongest, so it still misses promotion grade
- `tail_release_to_nonbottom_proportional` is the clearest `stronger-but-lower-quality` near-miss
  - headline CAGR jumps sharply and walk-forward remains positive at `3-1`
  - concentration and residual also improve
  - but drawdown worsens badly and Sharpe collapses, so it is not remotely promotion-grade
- `top2_split_49_51` is weaker than the hybrid challenger
  - it reduces concentration versus the strongest
  - but it does not preserve CAGR or walk-forward quality as well as the hybrid branch
- `alt_family_top3_flat_bonus18` confirms the outer boundary of the trade-off
  - it is the broadest challenger in this small set
  - but it loses far too much headline strength to remain a serious strongest candidate

## Verdict

- keep `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on` as the single aggressive strong branch
- treat `hybrid_top2_plus_third00125` as the current best `broader-but-weaker` challenger
- treat `bonus_schedule_first55_second45` as the current best `stronger-like but not promotion-grade` challenger
- treat `bonus_recipient_top1_third_85_15` as the current best `blended-quality but not promotion-grade` challenger
- treat `tail_skip_entry_flowweakest_new_bottom4_top25_mid75` as the current best `skip-entry stronger-like but lower-quality` challenger
- treat `tail_release_to_nonbottom_proportional` as the current best `stronger-but-much-lower-quality` challenger
- treat `top2_split_49_51` as an inferior micro-adjustment candidate
- treat `alt_family_top3_flat_bonus18` as a useful boundary check rather than a live promotion candidate
