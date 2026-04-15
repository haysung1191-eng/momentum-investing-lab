# Split Models Aggressive Branch Review

## Scope

- branch family: sector-constrained aggressive research variants
- retired comparison branches: `rule_sector_cap2_breadth_risk_off`, `rule_sector_cap2_breadth_it_risk_off`, `rule_sector_cap2_breadth_it_us5_cap`, `rule_sector_cap2_breadth_it_us5_top2_risk_on`
- surviving branch: `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on`

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
- `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on`
  - CAGR: `49.65%`
  - MDD: `-29.27%`
  - Sharpe: `1.6612`
  - Annual turnover: `14.88`

## Delta review

- months compared: `61`
- positive months for `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on` vs `rule_sector_cap2_breadth_it_us5_top2_risk_on`: `14`
- negative months: `9`
- average monthly net-return delta: `+0.191%p`
- best delta month: `2024-11-29 -> 2024-12-31`, `+3.31%p`
- worst delta month: `2023-05-31 -> 2023-06-30`, `-1.32%p`

## Weak-period review

- weak window: `2021-04-30 -> 2023-08-31`
- months compared: `25`
- baseline loss months: `11`
- loss months improved: `1`
- average monthly net-return delta: `+0.142%p`
- average loss-month delta: `+0.100%p`

## Prior top-slice concentration review

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

## Prior top-slice cost sensitivity review

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

## Convex top-slice cost sensitivity review

- even at `75 bps` one-way cost, `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on` remains the strongest aggressive branch in this family
- `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on`
  - CAGR at `75 bps`: `38.26%`
  - Sharpe at `75 bps`: `1.3626`
- `rule_sector_cap2_breadth_it_us5_top2_risk_on`
  - CAGR at `75 bps`: `35.76%`
  - Sharpe at `75 bps`: `1.3117`
- `rule_sector_cap2_breadth_it_us5_risk_on`
  - CAGR at `75 bps`: `31.82%`
  - Sharpe at `75 bps`: `1.2554`
- cost drag still exists, but the convex branch keeps its ranking edge even under harsher execution assumptions

## Convex top-slice walk-forward review

- 24-month / 12-month-step walk-forward windows compared: `4`
- `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on` beat `rule_sector_cap2_breadth_it_us5_top2_risk_on` on CAGR in `3` windows and lost in `0`
- average walk-forward CAGR delta vs `rule_sector_cap2_breadth_it_us5_top2_risk_on`: `+2.22%p`
- average walk-forward Sharpe delta: `+0.0458`
- strongest relative window: `2023-08-31 -> 2026-01-30`, CAGR delta `+4.60%p`
- even the weak window `2021-04-30 -> 2023-08-31` still showed a positive CAGR delta of `+1.09%p`
- interpretation: the convex branch does not rely on a single recent burst; its edge survives across rolling windows and is still present in the weaker regime slice

## Convex top-slice regime review

- the convex branch is still pro-cyclical, but its average edge does not disappear in down-market buckets
- versus `rule_sector_cap2_breadth_it_us5_top2_risk_on`:
  - `SPY UP` average monthly delta: `+0.177%p`
  - `SPY DOWN` average monthly delta: `+0.223%p`
  - `KOSPI UP` average monthly delta: `+0.336%p`
  - `KOSPI DOWN` average monthly delta: `+0.032%p`
- joint regime view:
  - `SPY UP / KOSPI UP`: `+0.277%p`
  - `SPY DOWN / KOSPI DOWN`: `+0.083%p`
  - `SPY DOWN / KOSPI UP`: `+0.747%p`
  - `SPY UP / KOSPI DOWN`: `-0.023%p`
- interpretation: the edge is strongest in broadly favorable tapes, but it is not just an up-market artifact; only the `SPY UP / KOSPI DOWN` mixed bucket is mildly negative on average

## Prior top-slice walk-forward review

- 24-month / 12-month-step walk-forward windows compared: `4`
- `rule_sector_cap2_breadth_it_us5_top2_risk_on` beat `rule_sector_cap2_breadth_it_us5_risk_on` on CAGR in `3` windows and lost in `0`
- average walk-forward CAGR delta vs `rule_sector_cap2_breadth_it_us5_risk_on`: `+4.20%p`
- average walk-forward Sharpe delta: `+0.0250`
- strongest relative window: `2023-08-31 -> 2026-01-30`, CAGR delta `+10.37%p`
- even the weak window `2021-04-30 -> 2023-08-31` still showed a positive CAGR delta of `+1.22%p`

## Prior top-slice regime review

- the top2 branch performs best in favorable regimes, but it still keeps a positive average delta in adverse regimes
- versus `rule_sector_cap2_breadth_it_us5_risk_on`:
  - `SPY UP` average monthly delta: `+0.454%p`
  - `SPY DOWN` average monthly delta: `+0.082%p`
  - `KOSPI UP` average monthly delta: `+0.518%p`
  - `KOSPI DOWN` average monthly delta: `+0.139%p`
- interpretation: the branch is pro-cyclical, but not purely regime-fragile; its edge compresses in weak markets rather than fully flipping negative on average

## Prior top-slice residual-edge review

- removing the three biggest winner-driven contributors `PLTR`, `NVDA`, and `MU` leaves only a small residual edge
- total average monthly delta vs `rule_sector_cap2_breadth_it_us5_risk_on`: `+0.338%p`
- average monthly delta attributable to `PLTR/NVDA/MU`: `+0.322%p`
- average residual monthly delta after excluding them: `+0.016%p`
- residual positive months: `12`
- residual negative months: `11`
- leave-one-out checks are less alarming: excluding any one of `PLTR`, `NVDA`, or `MU` still leaves a meaningful residual edge of roughly `+0.220%p` to `+0.241%p` with `15` positive vs `8` negative months
- interpretation: the branch still has a small residual edge beyond the top winners, but the practical alpha is overwhelmingly tied to a narrow US tech winner cluster

## Prior top-slice basket-decay review

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

## Convex top-slice concentration review

- versus `rule_sector_cap2_breadth_it_us5_top2_risk_on`, the new convex branch still avoids the single-shock-month failure mode but remains meaningfully concentrated
- months compared: `61`
- positive months: `14`
- negative months: `9`
- top 1 positive month share of total positive delta: `19.86%`
- top 3 positive month share: `54.96%`
- top 1 positive symbol share: `29.66%`
- top 3 positive symbol share: `68.17%`
- top symbols driving the edge: `NVDA`, `PLTR`, `MU`
- interpretation: month concentration is acceptable, but the incremental alpha still comes disproportionately from a narrow US winner cluster

## Convex top-slice basket-decay review

- cumulative winner-basket exclusions show the convex branch depends even more heavily on the top two winners than the prior strongest branch
- excluding only the top symbol `NVDA` still leaves average monthly residual delta of `+0.081%p`
- excluding the top two symbols `NVDA/PLTR` flips the residual edge slightly negative at `-0.015%p`
- excluding the top three symbols `NVDA/PLTR/MU` pushes residual delta further negative to `-0.062%p`
- residual month balance also degrades quickly:
  - top1 excluded: `11` positive vs `12` negative months
  - top2 excluded: `11` positive vs `12` negative months
  - top3 excluded: `9` positive vs `14` negative months
- interpretation: the new branch is stronger on headline performance, but it is also more explicitly dependent on a compact top-winner basket than the prior strongest branch

## Convex top-slice residual-edge review

- removing the three biggest winner-driven contributors `NVDA`, `PLTR`, and `MU` flips the residual edge negative
- total average monthly delta vs `rule_sector_cap2_breadth_it_us5_top2_risk_on`: `+0.191%p`
- average monthly delta attributable to `NVDA/PLTR/MU`: `+0.254%p`
- average residual monthly delta after excluding them: `-0.062%p`
- residual positive months: `9`
- residual negative months: `14`
- leave-one-out checks are still less alarming than the basket exclusion:
  - excluding `NVDA` leaves `+0.081%p`
  - excluding `PLTR` leaves `+0.095%p`
  - excluding `MU` leaves `+0.144%p`
- interpretation: the convex branch is not a single-name illusion, but its incremental alpha is overwhelmingly tied to a narrow `NVDA/PLTR/MU` winner cluster

## Interpretation

- the new convex top-slice overlay is a genuine structural improvement over the prior strongest branch: CAGR and Sharpe both improved again while MDD stayed flat and turnover fell slightly
- month-level improvement is still broad enough to stay out of the narrow-period reject bucket: `14` positive months versus `9` negative months with average monthly delta `+0.191%p`
- weak-period quality also improved slightly instead of getting worse: average weak-period delta stayed positive and loss-month average delta turned positive
- the cost-sensitivity check is supportive: even under `75 bps` one-way cost, the convex branch still leads both `top2_risk_on` and plain `risk_on`
- the walk-forward check is also supportive: convex stayed ahead of `top2_risk_on` in every non-tied rolling window and even kept a positive edge in the weak 2021-2023 slice
- the regime check is supportive: convex retains a positive average edge in both `SPY UP` and `SPY DOWN` buckets, with only one mixed joint-regime slice slightly negative
- the main remaining caution is stronger concentration: basket-decay and residual-edge checks both show that much of the incremental gain is even more dependent on the `NVDA/PLTR/MU` winner cluster than the prior strongest branch
- this remains a high-CAGR research branch, not an operational baseline candidate

## Verdict

- retire `rule_sector_cap2_breadth_risk_off`, `rule_sector_cap2_breadth_it_risk_off`, `rule_sector_cap2_breadth_it_us5_cap`, and `rule_sector_cap2_breadth_it_us5_top2_risk_on` from active aggressive research focus
- keep `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on` as the single aggressive strong branch
- keep operational baseline separate as `rule_breadth_it_us5_cap`
