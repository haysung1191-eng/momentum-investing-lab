# Split Models Nightly Safe Summary

## Purpose

- freeze the current strongest / challenger truth before another overnight research push
- make it easy to answer three questions quickly:
  - what is the current strongest branch
  - what is the current best broader challenger
  - why is the strongest still staying alive

## Current truth

- repo: `momentum`
- asset class: `stocks_etfs`
- operational baseline: `rule_breadth_it_us5_cap`
- aggressive strongest: `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
- broader challenger: `hybrid_top2_plus_third0025`

## Strongest snapshot

- CAGR: `63.16%`
- MDD: `-29.27%`
- Sharpe: `1.6892`
- Annual turnover: `15.32`

## Broader challenger snapshot

- variant: `hybrid_top2_plus_third0025`
- CAGR: `63.08%`
- MDD: `-29.26%`
- Sharpe: `1.6898`
- Annual turnover: `15.33`

## Why strongest still stays

- broader challenger still gives up headline strength:
  - CAGR delta vs strongest: `-0.08%p`
  - `75 bps` cost CAGR delta: `-0.08%p`
  - walk-forward: `2` positive CAGR windows, `2` negative
- broader challenger is still interesting:
  - Sharpe delta vs strongest: `+0.0006`
  - MDD delta vs strongest: `+0.01%p`
  - concentration is meaningfully lower than the strongest
- interpretation:
  - strongest is still the `stronger` branch
  - broader challenger is still the `broader-but-weaker` branch

## Benchmark guardrail

- benchmark: `benchmark_xs_mom_12_1_top5_eq`
- strongest `75 bps` CAGR delta vs benchmark: `+11.49%p`
- strongest start-date shift record: `5` positive CAGR windows, `0` negative

## Nightly verdict

- keep the current strongest as the mainline aggressive branch
- do not promote the broader challenger yet
- if more overnight work is run, prefer broader-challenger exploration over disturbing the strongest baseline again
