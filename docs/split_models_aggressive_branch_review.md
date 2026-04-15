# Split Models Aggressive Branch Review

## Scope

- branch family: sector-constrained aggressive research variants
- retired comparison branches: `rule_sector_cap2_breadth_risk_off`, `rule_sector_cap2_breadth_it_risk_off`, `rule_sector_cap2_breadth_it_us5_cap`
- surviving branch: `rule_sector_cap2_breadth_it_us5_top2_risk_on`

## Full-period comparison

- `rule_sector_cap2_breadth_it_us5_cap`
  - CAGR: `39.72%`
  - MDD: `-29.27%`
  - Sharpe: `1.5423`
  - Annual turnover: `14.57`
- `rule_sector_cap2_breadth_it_us5_risk_on`
  - CAGR: `42.80%`
  - MDD: `-29.27%`
  - Sharpe: `1.5776`
  - Annual turnover: `14.99`
- `rule_sector_cap2_breadth_it_us5_top2_risk_on`
  - CAGR: `47.05%`
  - MDD: `-29.27%`
  - Sharpe: `1.6165`
  - Annual turnover: `15.00`

## Delta review

- months compared: `61`
- positive months for `rule_sector_cap2_breadth_it_us5_top2_risk_on` vs `rule_sector_cap2_breadth_it_us5_risk_on`: `16`
- negative months: `7`
- average monthly net-return delta: `+0.338%p`
- best delta month: `2025-11-28 -> 2026-01-30`, `+5.75%p`
- worst delta month: `2023-07-31 -> 2023-08-31`, `-0.87%p`

## Weak-period review

- weak window: `2021-04-30 -> 2023-08-31`
- months compared: `25`
- baseline loss months: `11`
- loss months improved: `0`
- average monthly net-return delta: `+0.085%p`
- average loss-month delta: `-0.129%p`

## Concentration review

- months compared: `61`
- positive months: `16`
- negative months: `7`
- top 1 positive month share of total positive delta: `24.83%`
- top 3 positive month share: `46.06%`
- top 1 positive symbol share: `27.51%`
- top 3 positive symbol share: `74.91%`
- top symbols driving the edge: `PLTR`, `NVDA`, `MU`

## Concentration interpretation

- the month-level edge is not a single-month artifact, but it is still moderately concentrated in a handful of favorable months
- the symbol-level edge is much more concentrated than the month-level edge: most of the incremental alpha came from a small cluster of US information-technology winners
- that concentration is acceptable for an aggressive research branch, but it is a clear reason not to treat this as an operational baseline candidate

## Cost sensitivity review

- even at `75 bps` one-way cost, `rule_sector_cap2_breadth_it_us5_top2_risk_on` remains the best aggressive branch in this family
- `rule_sector_cap2_breadth_it_us5_top2_risk_on`
  - CAGR at `75 bps`: `35.76%`
  - Sharpe at `75 bps`: `1.3117`
- `rule_sector_cap2_breadth_it_us5_risk_on`
  - CAGR at `75 bps`: `31.82%`
  - Sharpe at `75 bps`: `1.2554`
- `rule_breadth_it_us5_cap`
  - CAGR at `75 bps`: `23.95%`
  - Sharpe at `75 bps`: `1.1090`
- cost drag is real, but the ranking survives; this reduces the chance that the top2 branch is only a low-friction backtest artifact

## Walk-forward review

- 24-month / 12-month-step walk-forward windows compared: `4`
- `rule_sector_cap2_breadth_it_us5_top2_risk_on` beat `rule_sector_cap2_breadth_it_us5_risk_on` on CAGR in `3` windows and lost in `0`
- average walk-forward CAGR delta vs `rule_sector_cap2_breadth_it_us5_risk_on`: `+4.20%p`
- average walk-forward Sharpe delta: `+0.0250`
- strongest relative window: `2023-08-31 -> 2026-01-30`, CAGR delta `+10.37%p`
- even the weak window `2021-04-30 -> 2023-08-31` still showed a positive CAGR delta of `+1.22%p`

## Regime review

- the top2 branch performs best in favorable regimes, but it still keeps a positive average delta in adverse regimes
- versus `rule_sector_cap2_breadth_it_us5_risk_on`:
  - `SPY UP` average monthly delta: `+0.454%p`
  - `SPY DOWN` average monthly delta: `+0.082%p`
  - `KOSPI UP` average monthly delta: `+0.518%p`
  - `KOSPI DOWN` average monthly delta: `+0.139%p`
- interpretation: the branch is pro-cyclical, but not purely regime-fragile; its edge compresses in weak markets rather than fully flipping negative on average

## Residual-edge review

- removing the three biggest winner-driven contributors `PLTR`, `NVDA`, and `MU` leaves only a small residual edge
- total average monthly delta vs `rule_sector_cap2_breadth_it_us5_risk_on`: `+0.338%p`
- average monthly delta attributable to `PLTR/NVDA/MU`: `+0.322%p`
- average residual monthly delta after excluding them: `+0.016%p`
- residual positive months: `12`
- residual negative months: `11`
- leave-one-out checks are less alarming: excluding any one of `PLTR`, `NVDA`, or `MU` still leaves a meaningful residual edge of roughly `+0.220%p` to `+0.241%p` with `15` positive vs `8` negative months
- interpretation: the branch still has a small residual edge beyond the top winners, but the practical alpha is overwhelmingly tied to a narrow US tech winner cluster

## Basket-decay review

- cumulative winner-basket exclusions show the edge decays fast once the top US tech cluster is stripped out
- excluding only the top symbol `PLTR` still leaves average monthly residual delta of `+0.220%p`
- excluding the top two symbols `PLTR/NVDA` leaves `+0.113%p`
- excluding the top three symbols `PLTR/NVDA/MU` leaves only `+0.016%p`
- excluding the top four symbols `PLTR/NVDA/MU/LRCX` flips the residual edge slightly negative at `-0.028%p`
- residual month balance also collapses with basket size:
  - top1 excluded: `15` positive vs `8` negative months
  - top2 excluded: `13` positive vs `10` negative months
  - top3 excluded: `12` positive vs `11` negative months
  - top4 excluded: `11` positive vs `12` negative months
- interpretation: the branch is not a single-name illusion, but it is meaningfully dependent on a compact winner basket rather than a broad-based residual edge

## Interpretation

- the top-slice risk-on overlay is a genuine new branch, not a cosmetic tweak: full-period CAGR and Sharpe both improved while MDD stayed flat
- month-level improvement is broad enough to avoid the prior "single-shock-month" failure mode
- the main caveats are weak-period quality and concentration: average weak-period return still improved slightly, but loss months were still a bit worse on average, and most of the incremental alpha came from a small set of US IT winners
- the cost-sensitivity check is supportive: the branch still leads this family even under much harsher one-way cost assumptions
- the walk-forward check is also supportive: the branch kept a positive CAGR edge in every non-tied rolling window versus the prior aggressive branch
- the regime check is supportive: most of the edge appears in up markets, but the average delta stays positive even in down-market buckets
- the residual-edge check is cautionary: most of the incremental alpha disappears once the top three winner symbols are stripped out, even though no single winner alone explains the whole edge
- the basket-decay check is more explicit: the residual alpha degrades quickly from top1 to top4 exclusions, which confirms that this branch should be treated as a concentrated aggressive research branch rather than a generally transferable overlay
- this remains a high-CAGR research branch, not an operational baseline candidate

## Verdict

- retire `rule_sector_cap2_breadth_risk_off`, `rule_sector_cap2_breadth_it_risk_off`, and `rule_sector_cap2_breadth_it_us5_cap` from active aggressive research focus
- keep `rule_sector_cap2_breadth_it_us5_top2_risk_on` as the single aggressive strong branch
- keep operational baseline separate as `rule_breadth_it_us5_cap`
