# Momentum Investing Lab

Research-first momentum investing lab for stocks and ETFs.

This repository is not a single backtest script. It is a working research record with:

- strategy branches
- promotion / retirement history
- benchmark reviews
- walk-forward and cost checks
- shadow-operations scaffolding for KIS-based live transition

The current emphasis is on two tracks:

- a robustness-first operational baseline
- a higher-CAGR aggressive research branch

## Current state

### Operational baseline

- Variant: `rule_breadth_it_us5_cap`
- Role: practical baseline / robustness-first model
- Latest headline metrics:
  - CAGR: `33.43%`
  - MDD: `-25.24%`
  - Sharpe: `1.4482`

### Aggressive research strongest

- Variant: `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
- Role: current strongest mixed-universe aggressive branch
- Latest headline metrics:
  - CAGR: `63.16%`
  - MDD: `-29.27%`
  - Sharpe: `1.6892`

Important interpretation:

- the aggressive strongest is strong in the full mixed universe
- it is not a universal stock-only winner
- it still carries compact winner-basket dependence

## Why this repo may be useful

Many trading repos show one "best" backtest and stop there.

This repo tries to keep the full research trail visible:

- what was tested
- what was promoted
- what was killed
- why a branch survived
- where the model is still fragile

That is why the repo includes not only code, but also promotion ledgers, benchmark reviews, universe-split reviews, and branch-search summaries.

## What is already validated

For the current aggressive strongest, the repo already tracks:

- full-period comparison
- walk-forward comparison
- cost sensitivity
- benchmark-relative comparison
- start-date shift checks
- universe-split review
- promotion ledger
- branch-search / survivor summary

This makes the current strongest more defensible than a plain "highest CAGR wins" workflow.

## Repo map

### Core strategy and runtime

- `split_models/`
  - aggressive branch family and promotion path
- `live_core/`
  - shared runtime, screener helpers, metrics, universe handling
- `main.py`
  - thin runtime entrypoint
- `screener.py`
  - compatibility shim for the screener implementation

### Research and analysis

- `tools/analysis/`
  - benchmark, promotion, plateau, and search-summary analysis scripts
- `tools/research/`
  - one-off research and evaluation scripts
- `tools/pipelines/`
  - research pipeline orchestration
- `tools/data_ingestion/`
  - backfill and cache-building scripts

### Shadow / operating path

- `kis_shadow_portfolio.py`
- `kis_shadow_rebalance_diff.py`
- `kis_shadow_health.py`
- `kis_shadow_ops_summary.py`
- `kis_micro_live_order_sheet.py`

These support shadow trading and operator handoff. They are not yet a full unattended auto-execution stack.

### Documentation

- `docs/split_models_aggressive_branch_review.md`
- `docs/split_models_external_benchmark_review.md`
- `docs/split_models_universe_split_review.md`
- `docs/split_models_promotion_ledger.md`
- `docs/split_models_branch_search_history.md`
- `docs/split_models_search_summary_review.md`
- `docs/split_models_promotion_plateau_review.md`

## Best reading order

If you are new to the repo, read in this order:

1. `docs/split_models_aggressive_branch_review.md`
2. `docs/split_models_external_benchmark_review.md`
3. `docs/split_models_universe_split_review.md`
4. `docs/split_models_promotion_ledger.md`
5. `docs/split_models_branch_search_history.md`
6. `docs/split_models_search_summary_review.md`

This gives you:

- what the current strongest is
- why it survived
- what it beats
- where it is still weak
- how large the search tree was

## Quick start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run a focused test

```bash
python -m pytest tests/test_split_models_backtest.py -q
```

### 3. Rebuild benchmark review

```bash
python tools/analysis/analyze_split_models_external_benchmarks.py
python tools/analysis/analyze_split_models_benchmark_walkforward.py
python tools/analysis/analyze_split_models_benchmark_cost.py
python tools/analysis/analyze_split_models_benchmark_start_shift.py
```

### 4. Rebuild promotion and universe reviews

```bash
python tools/analysis/analyze_split_models_universe_split.py
python tools/analysis/analyze_split_models_promotion_ledger.py
python tools/analysis/analyze_split_models_search_summary.py
```

## What this repo is not

- not a promise of live trading alpha
- not a finished auto-trading product
- not a single clean universal stock-only model
- not a formal multiple-testing correction framework

The repo is best understood as:

- a transparent momentum research lab
- a branch-selection and robustness-tracking workflow
- a partial bridge from research to shadow operations

## Current limitation

The biggest open problem is not "can CAGR go higher?"

It is:

- can the aggressive strongest keep its edge
- while reducing dependence on a narrow winner basket

That is the main live research question still open in this repo.

## License / usage note

Use this repository as research infrastructure and documentation of model selection logic, not as direct investment advice.
