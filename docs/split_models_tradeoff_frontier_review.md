# Split Models Tradeoff Frontier Review

## Scope

- compare the current aggressive strongest branch against recent nearby challengers that trade headline strength for broader edge
- current strongest:
  - `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
- challenger set:
  - `hybrid_top2_plus_third00125`
  - `bonus_schedule_first55_second45`
  - `bonus_recipient_top1_third_67_33`
  - `tail_skip_entry_flowweakest_new_bottom4_top50_mid50`
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
- `bonus_recipient_top1_third_67_33`
  - CAGR: `63.21%`
  - MDD: `-29.09%`
  - Sharpe: `1.7018`
  - Annual turnover: `15.94`
  - walk-forward: `2` positive CAGR windows, `2` negative
  - `75 bps` CAGR delta vs strongest: `-0.46%p`
  - top 3 positive symbol share: `35.09%`
- `tail_skip_entry_flowweakest_new_bottom4_top50_mid50`
  - CAGR: `63.75%`
  - MDD: `-29.23%`
  - Sharpe: `1.6636`
  - Annual turnover: `14.72`
  - walk-forward: `3` positive CAGR windows, `1` negative
  - `75 bps` CAGR delta vs strongest: `+1.04%p`
  - top 3 positive symbol share: `48.02%`
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
- `bonus_recipient_top1_third_67_33` is the best `higher-quality` near-miss
  - Sharpe improves materially and drawdown improves as well
  - concentration drops a lot versus the strongest
  - but turnover jumps and `75 bps` cost CAGR turns negative, so it also misses promotion grade
- `tail_skip_entry_flowweakest_new_bottom4_top50_mid50` is the best `skip-entry stronger-like` near-miss
  - CAGR, breadth, and turnover all improve versus the strongest
  - walk-forward also stays mostly positive at `3-1`
  - but Sharpe remains meaningfully lower than the strongest, so it still misses promotion grade
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
- treat `bonus_recipient_top1_third_67_33` as the current best `higher-quality but cost-weaker` challenger
- treat `tail_skip_entry_flowweakest_new_bottom4_top50_mid50` as the current best `skip-entry stronger-like but lower-quality` challenger
- treat `top2_split_49_51` as an inferior micro-adjustment candidate
- treat `alt_family_top3_flat_bonus18` as a useful boundary check rather than a live promotion candidate
