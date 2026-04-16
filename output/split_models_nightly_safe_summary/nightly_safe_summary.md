# Split Models Nightly Safe Summary

## Current truth

- repo: `momentum`
- asset class: `stocks_etfs`
- operational baseline: `rule_breadth_it_us5_cap`
- aggressive strongest: `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
- broader challenger: `hybrid_top2_plus_third00125`

## Strongest snapshot

- CAGR: `63.16%`
- MDD: `-29.27%`
- Sharpe: `1.6892`
- Annual turnover: `15.32`

## Broader challenger snapshot

- variant: `hybrid_top2_plus_third00125`
- CAGR: `63.12%`
- MDD: `-29.27%`
- Sharpe: `1.6895`
- Annual turnover: `15.32`

## Why strongest still stays

- CAGR delta vs strongest: `-0.04%p`
- MDD delta vs strongest: `+0.00%p`
- Sharpe delta vs strongest: `+0.0003`
- `75 bps` cost CAGR delta: `-0.04%p`
- walk-forward: `2 positive / 2 negative`

## Benchmark guardrail

- benchmark: `benchmark_xs_mom_12_1_top5_eq`
- strongest `75 bps` CAGR delta vs benchmark: `+11.49%p`
- strongest start-date shift record: `5 positive / 0 negative`

## Nightly verdict

- keep the current strongest as the mainline aggressive branch
- treat the broader challenger as a near-miss, not a promotion
- if more overnight work is run, prefer broader-challenger exploration over disturbing the strongest baseline again
