# Momentum Investing Lab

Research-first momentum investing lab for stocks and ETFs.

This repository is a public research record for how a mixed-universe momentum model is explored, promoted, killed, and defended over time. It is built around one practical baseline, one current aggressive strongest branch, and a growing audit trail for why alternatives survived or failed.

## What This Repo Does

- builds and compares momentum variants across KR/US stocks and ETFs
- tracks promotion decisions instead of only showing one best backtest
- checks full-period, walk-forward, cost, and fragility tradeoffs
- keeps dead families and near-miss families visible
- includes shadow-operations scaffolding for eventual live transition

If you want the short version:

- operational baseline = robustness-first
- aggressive strongest = highest-conviction current research branch
- current work = find a branch that beats the strongest without breaking drawdown, cost robustness, or fragility

## Current Truth

### Operational baseline

- Variant: `rule_breadth_it_us5_cap`
- Role: robustness-first operating baseline
- CAGR: `33.43%`
- MDD: `-25.24%`
- Sharpe: `1.4482`

### Aggressive research strongest

- Variant: `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
- Role: current strongest mixed-universe aggressive branch
- CAGR: `63.16%`
- MDD: `-29.27%`
- Sharpe: `1.6892`
- Annual Turnover: `15.32`

## Current Near-Miss Map

These are the main challenger axes that currently matter.

| Axis | Variant | Why it matters | Why it is not promoted |
| --- | --- | --- | --- |
| Broader | `hybrid_top2_plus_third00125` | broader exposure | weaker overall |
| Quality | `bonus_recipient_top1_third_85_15` | best blended-quality extension | still not promotion-grade |
| Headline | `tail_skip_entry_flowweakest_new_bottom4_top25_mid75` | best lower-turnover headline extension | quality still weaker |
| Defensive weighting | `regime_weight_defensive_if_top2flowsoft` | closest defensive weighting point | cost / fragility still weaker |
| Stronger-but-more-fragile | `multi_step_confirm_top1_flowtop2` | stronger on headline and Sharpe | concentration worsens too much |
| Redistribution | `tail_release_top50_mid50` | strongest aggressive redistribution contender | drawdown too weak for promotion |

## Why This Repo Is Different

Many strategy repositories stop at “here is the best CAGR”.

This one keeps the full decision trail visible:

- what was tested
- what got promoted
- what got killed
- what is saturated or no-op
- what still looks promising but is too fragile

That means the repository contains not only strategy code, but also:

- tradeoff frontier reviews
- promotion-defense refreshes
- dead-family ledgers
- family saturation reviews
- trade and price-data audit reports

## What The Models Actually Traded

The repository now includes an explicit trade/data audit layer so the research is not only “metrics on paper”.

Latest strongest trade snapshot currently shows:

- latest signal date: `2026-01-30`
- entered: `0000J0, CAT, GILD, GS, JNJ, LMT`
- exited: `360750, BIIB, C, LLY, LRCX, MU`

Latest strongest top holdings snapshot includes:

- `KR:069500`
- `KR:0000J0`
- `US:LMT`
- `US:CAT`
- `US:JNJ`

See:

- [Trade and Data Audit](docs/split_models_trade_data_audit.md)
- [Trade/Data Audit Output](output/split_models_trade_data_audit/trade_data_audit.md)

## Why Trust The Backtests At All?

Healthy skepticism is warranted. This repo does not assume that a backtest is trustworthy just because a number is high.

The current workflow explicitly tracks:

- full-period comparison
- walk-forward comparison
- cost sensitivity
- promotion-defense reasoning
- dead/no-op family elimination
- sample price-file integrity checks for traded symbols

Price data is currently read from local cached `csv.gz` files under `data/`, not from a live API call at review time. The audit layer checks sample traded symbols for:

- file existence
- date range
- row count
- duplicate dates
- nonpositive close rows

Good starting links:

- [Promotion Defense Refresh](docs/split_models_promotion_defense_refresh.md)
- [Tradeoff Frontier Review](docs/split_models_tradeoff_frontier_review.md)
- [Dead Family Ledger](docs/split_models_dead_family_ledger.md)
- [Redistribution Family Review](docs/split_models_redistribution_family_review.md)

## Repo Map

### Core strategy and runtime

- `split_models/`
- `live_core/`
- `main.py`
- `screener.py`

### Research and analysis

- `tools/analysis/`
- `tools/research/`
- `tools/pipelines/`
- `tools/data_ingestion/`

### Shadow / operating path

- `kis_shadow_portfolio.py`
- `kis_shadow_rebalance_diff.py`
- `kis_shadow_health.py`
- `kis_shadow_ops_summary.py`
- `kis_micro_live_order_sheet.py`

### Key docs

- `docs/split_models_aggressive_branch_review.md`
- `docs/split_models_promotion_defense_refresh.md`
- `docs/split_models_tradeoff_frontier_review.md`
- `docs/split_models_dead_family_ledger.md`
- `docs/split_models_trade_data_audit.md`

## Best Reading Order

If you are new here, read in this order:

1. `docs/split_models_aggressive_branch_review.md`
2. `docs/split_models_promotion_defense_refresh.md`
3. `docs/split_models_tradeoff_frontier_review.md`
4. `docs/split_models_dead_family_ledger.md`
5. `docs/split_models_trade_data_audit.md`

This gives you:

- what the current strongest is
- why it still survives
- what nearly replaced it
- what should no longer be searched
- what the model actually traded
- what price-data source was audited

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run a focused backtest test

```bash
python -m pytest tests/test_split_models_backtest.py -q
```

### 3. Rebuild current-truth analysis

```bash
python tools/analysis/analyze_split_models_tradeoff_frontier.py
python tools/analysis/analyze_split_models_promotion_defense_refresh.py
python tools/analysis/analyze_split_models_dead_family_ledger.py
python tools/analysis/analyze_split_models_trade_data_audit.py
```

## What This Repo Is Not

- not investment advice
- not a finished auto-trading product
- not a claim that the aggressive strongest is universally best everywhere
- not a formal multiple-testing correction framework

The repo is best understood as:

- a transparent momentum research lab
- a model-promotion and failure-analysis workflow
- a bridge from research toward shadow operations

## Current Open Question

The main open question is no longer “can CAGR go higher?”

It is:

- can a new branch beat the current strongest
- without losing too much drawdown quality
- while keeping walk-forward, cost, and fragility acceptable

That is the central research problem this repository is still trying to solve.
