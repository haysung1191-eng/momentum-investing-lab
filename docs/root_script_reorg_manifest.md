# Root Script Reorg Manifest

## Why

The repository root has grown into a mixed landing zone for research scripts, operator tools, data ingestion jobs, dashboards, and entrypoints. This manifest defines the first safe reorganization boundary before any physical file moves happen.

The goal is to reduce root-level clutter without breaking imports or CLI entrypoints. We are explicitly separating:

- research analysis scripts
- data ingestion / backfill scripts
- operator and archive tooling
- pipeline runners
- dashboards
- root/core modules that should stay put until a later dependency pass

## Current Inventory

Machine-readable inventory:

- [root_script_inventory.csv](/C:/AI/momentum/output/repo_script_manifest/root_script_inventory.csv)
- [root_script_inventory_summary.json](/C:/AI/momentum/output/repo_script_manifest/root_script_inventory_summary.json)

Current root Python file count: `37`

Category counts:

- `research`: `6`
- `operations`: `6`
- `data_ingestion`: `0`
- `core`: `17`
- `pipelines`: `2`
- `uncategorized`: `6`

Completed so far:

- all `analyze_split_models_*.py` scripts were moved out of root into `tools/analysis`
- all split-model `build_*`, `check_*`, and `archive_*` operator scripts were moved out of root into `tools/operations`
- all split-model `run_*` pipeline scripts were moved out of root into `tools/pipelines`
- all `*_backfill.py`, `build_*cache.py`, and `refresh_*` ingestion scripts were moved out of root into `tools/data_ingestion`
- all current `kis_*_eval.py`, `kis_*_compare.py`, `kis_*_report.py`, `us_*`, `backtest_*`, and `event_*` research scripts were moved out of root into `tools/research`
- `plot_us_momentum_paper_figures.py` was moved out of root into `tools/plotting`

## Proposed Target Layout

- `tools/analysis`
  - `analyze_*` scripts and split-model robustness/benchmark studies
- `tools/research`
  - research-only backtests, evals, compare/report utilities, US-specific strategy experiments
- `tools/data_ingestion`
  - `*_backfill.py`, cache builders, metadata refresh, data coverage refresh
- `tools/operations`
  - `build_*`, `check_*`, `archive_*`, operator packet/readiness/drift helpers, monthly packet publishing
- `tools/pipelines`
  - `run_*` scripts that orchestrate multi-step flows
- `tools/plotting`
  - figure-generation scripts
- `tools/dashboards`
  - dashboard launchers that are not app entrypoints

## Hold In Place For Now

These should not move in the first wave because they are likely imported broadly or act as user-facing entrypoints:

- `config.py`
- `main.py`
- `dashboard.py`
- `screener.py`
- `shadow_dashboard.py`
- `split_models_shadow_dashboard.py`
- `kis_api.py`
- `kis_backtest_from_prices.py`
- `kis_flow_data.py`
- `kis_flow_signal.py`
- `kis_quality_data.py`
- `kis_shadow_common.py`
- `kis_shadow_*` shared modules

## First Safe Move Wave

The safest first relocation wave is scripts that are root-level CLIs and have low import risk:

1. data-ingestion and research script waves

Why this wave first:

- these files already behave like standalone utilities
- they mostly consume repo modules rather than being imported as shared libraries
- they align directly with the new folder taxonomy

## Second Move Wave

After split-model, data-ingestion, and research tools stabilized:

1. `plot_us_momentum_paper_figures.py` -> `tools/plotting` (completed)

## Manual Review Bucket

These currently remain uncategorized and need a human placement decision before moving:

- `config.py`
- `dashboard.py`
- `main.py`
- `screener.py`
- `shadow_dashboard.py`
- `split_models_shadow_dashboard.py`

Recommended handling:

- keep `config.py` and `main.py` in root for now
- decide later whether dashboards should live under `app/` or `tools/dashboards`
- keep `screener.py` in root until its dependency graph is inspected

## Move Rules

Before any real move:

1. Move one category at a time.
2. Update imports and CLI references in the same commit.
3. Add or update smoke tests for moved entrypoints.
4. Keep backwards-compatible stubs only if an external script or automation depends on the old path.
5. Prefer manifest-driven moves over ad hoc renames.

## Next Step

The next highest-value move is the manual-review/dashboard bucket:

- inspect `dashboard.py`, `shadow_dashboard.py`, and `split_models_shadow_dashboard.py` for `tools/dashboards` readiness
- inspect `screener.py` for dependency-heavy root coupling
- keep `config.py` and `main.py` in root unless a later entrypoint pass proves otherwise
