# Split Models Overnight Guardrail

## Purpose

- freeze the overnight triage rule before another search run
- keep the project from promoting a candidate just because one axis looks good

## Current truth

- repo: `momentum`
- asset class: `stocks_etfs`
- operational baseline: `rule_breadth_it_us5_cap`
- aggressive strongest: `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
- broader challenger: `hybrid_top2_plus_third00125`
- quality near-miss: `bonus_recipient_top1_third_75_25`
- headline near-miss: `tail_skip_entry_flowweakest_new_bottom4_top25_mid75`

## Kill Immediately

- full-period CAGR is below the strongest by more than 0.50%p
- walk-forward CAGR windows are net negative
- 75 bps cost CAGR delta vs strongest is negative by more than 0.25%p
- residual ex PLTR/NVDA/MU turns clearly negative

## Deeper Validation

- full-period CAGR delta vs strongest is non-negative
- walk-forward CAGR windows are at least 3 positive and no more than 1 negative
- 75 bps cost CAGR delta vs strongest is non-negative
- residual ex PLTR/NVDA/MU is non-negative

## Document As Near-Miss

- the candidate clearly wins one axis such as broader, higher-quality, or lower-turnover
- but it still fails promotion robustness on walk-forward, cost-adjusted Sharpe, or drawdown

## Axis Reading

- stronger axis: `headline CAGR plus promotion robustness`
- broader axis: `lower concentration and better breadth with only small CAGR give-up`
- quality axis: `higher Sharpe and better MDD even if turnover or cost-adjusted CAGR worsens`
- headline axis: `higher CAGR and lower turnover even if Sharpe stays weaker`

## Default Overnight Rule

- keep the current strongest unless a candidate clears the stronger-axis gate across full-period, walk-forward, cost, and residual together
