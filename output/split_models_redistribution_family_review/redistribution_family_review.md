# Split Models Redistribution Family Review

## Scope

- freeze the validated tail-release redistribution family in one place
- strongest reference: `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
- reviewed family points:
  - `top0 / mid100`
  - `top25 / mid75`
  - `top50 / mid50`

## Family Pattern

- all reviewed redistribution points produce much higher headline CAGR than the strongest
- adding some top2 share improves Sharpe, cost response, and turnover materially
- the family stays non-promotable because drawdown remains too weak even at the best blended point

## Best Headline Point

- variant: `tail_release_top50_mid50`
- CAGR: `76.47%`
- MDD: `-34.64%`
- Sharpe: `1.6967`
- walk-forward: `4 positive / 0 negative`
- `75 bps` cost CAGR delta vs strongest: `13.13%p`

## Best Quality Point

- variant: `tail_release_top50_mid50`
- CAGR: `76.47%`
- MDD: `-34.64%`
- Sharpe: `1.6967`
- walk-forward: `4 positive / 0 negative`
- walk-forward Sharpe delta: `+0.0503`

## Best Drawdown Point

- variant: `tail_release_top25_mid75`
- CAGR: `75.55%`
- MDD: `-34.01%`
- Sharpe: `1.6951`
- walk-forward: `4 positive / 0 negative`

## Best Blended Point

- variant: `tail_release_top50_mid50`
- CAGR: `76.47%`
- MDD: `-34.64%`
- Sharpe: `1.6967`
- Annual turnover: `14.41`
- walk-forward: `4 positive / 0 negative`
- `75 bps` cost CAGR delta vs strongest: `13.13%p`
- `75 bps` cost Sharpe delta vs strongest: `+0.0593`

## Interpretation

- `top0 / mid100` is the raw boundary point: very strong headline, but quality collapses too much
- `top25 / mid75` improves quality a lot while keeping very strong headline support
- `top50 / mid50` is the best blended redistribution point because Sharpe, walk-forward, cost, and turnover all remain strong
- even `top50 / mid50` still fails promotion grade because drawdown deterioration is too large

## Verdict

- keep `tail_release_top50_mid50` as the redistribution-family current truth
- treat the whole redistribution family as a strong but non-promotable aggressive frontier
- stop re-litigating this family unless a new drawdown-control axis is introduced
