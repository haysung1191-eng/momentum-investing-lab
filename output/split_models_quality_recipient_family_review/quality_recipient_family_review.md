# Split Models Quality Recipient Family Review

## Scope

- freeze the validated `top1 / top3` bonus-recipient family in one place
- strongest reference: `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
- reviewed family points:
  - `67 / 33`
  - `75 / 25`
  - `80 / 20`
  - `85 / 15`
  - `90 / 10`

## Family Pattern

- moving from `67 / 33` toward `90 / 10` increases raw CAGR steadily
- the same move also pushes walk-forward Sharpe robustness lower
- concentration rises as the split becomes more top1-heavy
- the family does not produce a promotion-grade strongest replacement

## Best Quality Point

- variant: `bonus_recipient_top1_third_67_33`
- CAGR: `63.21%`
- MDD: `-29.09%`
- Sharpe: `1.7018`
- walk-forward: `2 positive / 2 negative`
- `75 bps` cost CAGR delta vs strongest: `-0.46%p`

## Best Blended Point

- variant: `bonus_recipient_top1_third_85_15`
- CAGR: `65.43%`
- MDD: `-29.52%`
- Sharpe: `1.6927`
- walk-forward: `3 positive / 1 negative`
- walk-forward Sharpe delta: `-0.0124`
- `75 bps` cost CAGR delta vs strongest: `1.68%p`

## Best Headline Point

- variant: `bonus_recipient_top1_third_90_10`
- CAGR: `66.03%`
- MDD: `-29.65%`
- Sharpe: `1.6896`
- walk-forward: `3 positive / 1 negative`
- walk-forward Sharpe delta: `-0.0176`
- `75 bps` cost CAGR delta vs strongest: `2.26%p`

## Interpretation

- `67/33` is the best pure quality point, but it gives up too much headline strength
- `85/15` is the best blended point because it keeps the strongest mix of CAGR, cost support, and still-reasonable robustness
- `90/10` is the headline boundary point: stronger raw CAGR, but weaker robustness than `85/15`

## Verdict

- keep `bonus_recipient_top1_third_85_15` as the quality/blended near-miss current truth
- stop re-litigating this family unless a new validation axis is introduced
- move future search effort to a different family rather than pushing `top1 / top3` more aggressively
