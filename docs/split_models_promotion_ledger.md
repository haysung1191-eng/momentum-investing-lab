# Split Models Promotion Ledger

## Scope

- retired strongest branch: `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on`
- current strongest branch: `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_risk_on`
- purpose:
  - make the latest aggressive promotion legible in one place
  - show which axes actually justified the promotion
  - separate "promote" evidence from remaining caution

## Promotion summary

- promote `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_risk_on`
- retire `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on`
- reason:
  - ranked-tail source improved full-period CAGR and Sharpe while leaving MDD flat
  - walk-forward stayed positive on CAGR in `3` windows and lost in `0`
  - cost advantage survived through `75 bps`
  - residual-edge and basket-decay fragility improved instead of worsening
- caution:
  - the branch is still a mixed-universe aggressive construction rule
  - it is still not a stock-only winner

## Promotion ledger

| Axis | Baseline | Candidate | Delta | Verdict | Note |
| --- | ---: | ---: | ---: | --- | --- |
| Full-period CAGR | `49.65%` | `51.27%` | `+1.62%p` | promote | headline CAGR improved without extra drawdown |
| Full-period Sharpe | `1.6612` | `1.6691` | `+0.0079` | promote | Sharpe improved while MDD stayed flat |
| Walk-forward avg CAGR delta | `0.00%p` | `+1.61%p` | `+1.61%p` | promote | positive CAGR windows `3`, negative `0` |
| Cost latest CAGR delta | `0.00%p` | `+1.45%p` | `+1.45%p` | promote | still ahead at `75 bps` |
| Residual edge after top-3 winner removal | `-0.062%p` | `+0.018%p` | `+0.080%p` | promote | top-3 exclusion no longer flips residual edge negative |
| Basket decay after top-3 winner removal | `-0.062%p` | `+0.018%p` | `+0.080%p` | promote | basket decay is slower at the same exclusion depth |
| Hard benchmark CAGR delta at `75 bps` | `-0.71%p` | `+0.74%p` | `+1.45%p` | promote | candidate stays ahead of `12-1 full-universe top5` even under high cost |
| Full-universe CAGR delta vs retired strongest | `0.00%p` | `+1.62%p` | `+1.62%p` | promote | strongest family edge improved where the branch family is actually strongest |
| Stock-only CAGR delta vs retired strongest | `0.00%p` | `0.00%p` | `0.00%p` | caution | branch remains mixed-universe; ranked-tail did not create a new stock-only edge |

## Interpretation

- this promotion was not based on headline CAGR alone
- the ranked-tail branch improved on every axis that mattered for promotion:
  - full-period quality
  - walk-forward
  - cost
  - winner-basket fragility
  - hard benchmark defense
- the main thing that did **not** change is scope:
  - this is still strongest as a mixed-universe aggressive branch
  - it should not be oversold as a universal stock-only model

## Verdict

- treat the ranked-tail branch as a real strongest-branch promotion
- use the ledger together with:
  - `docs/split_models_aggressive_branch_review.md`
  - `docs/split_models_branch_search_history.md`
- keep the caution language intact:
  - strongest aggressive branch
  - mixed-universe construction rule
  - still concentration-aware, not operational baseline material
