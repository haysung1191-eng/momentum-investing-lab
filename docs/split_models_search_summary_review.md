# Split Models Search Summary Review

## Scope

- convert the branch-search log into a simple quantitative search summary
- objective:
  - make the search tree less opaque
  - show how many branches were actually explored
  - show how often branches were killed, retired, or kept

## Search inventory summary

- total branches documented: `35`
- total survivors: `2`
- total retired mainline branches: `13`
- total killed branches: `20`
- exploratory branches: `17`
- cosmetic branches: `3`

## By track

### Operational track

- documented branches: `4`
- survivors: `1`
- retired mainline branches: `3`
- killed exploratory branches: `0`
- survivor rate: `25.0%`

### Aggressive track

- documented branches: `31`
- survivors: `1`
- retired mainline branches: `10`
- killed branches: `20`
- exploratory branches: `17`
- cosmetic branches: `3`
- survivor rate: `3.2%`
- killed rate: `64.5%`

## Kill-reason concentration

- `weaker_cagr_and_sharpe`: `5`
- `dominated_by_top2_risk_on`: `3`
- `effectively_identical`: `3`
- `weaker_quality_metrics`: `2`
- all other reasons: `1` each

## Interpretation

- the aggressive search was not a tiny or trivial branch tree
- most aggressive branches did **not** survive:
  - only `1` of `31` documented aggressive branches remains active
  - `20` were explicitly killed
- this helps the project in one way:
  - the final aggressive branch was not selected from a cosmetic or unfiltered search where every small tweak was preserved
- but it also sharpens the selection-bias warning:
  - the current aggressive survivor emerged from a materially non-trivial search space
  - that means branch-history transparency is helpful, but it is not a statistical innocence proof

## Practical research reading

- operational selection looks relatively defensible:
  - small branch tree
  - explicit robustness-first promotion logic
- aggressive selection looks meaningfully more vulnerable:
  - larger search space
  - low survivor rate
  - final branch still carries winner-basket dependence even after the softer ranked-tail promotion

## Verdict

- use this summary as a quantitative companion to the branch-search log
- cite it when explaining that weak and cosmetic branches were aggressively filtered out
- do not oversell it as a formal multiple-testing correction
