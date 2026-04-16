# Split Models Promotion Ledger

## Scope

- retired strongest branch: `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count5_pen55_floor35_risk_on`
- current strongest branch: `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count5_pen50_floor30_risk_on`
- purpose:
  - make the latest aggressive promotion legible in one place
  - show which axes actually justified the promotion
  - separate "promote" evidence from remaining caution

## Promotion summary

- promote `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count5_pen50_floor30_risk_on`
- retire `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count5_pen55_floor35_risk_on`
- reason:
  - broader softer ranked-tail source improved full-period CAGR and Sharpe while leaving MDD flat
  - walk-forward stayed positive on CAGR in `3` windows and lost in `0`
  - cost advantage survived through `75 bps`
  - benchmark-relative strength improved again while concentration still stayed compact-winner heavy
- caution:
  - the branch is still a mixed-universe aggressive construction rule
  - it is still not a stock-only winner

## Promotion ledger

| Axis | Baseline | Candidate | Delta | Verdict | Note |
| --- | ---: | ---: | ---: | --- | --- |
| Full-period CAGR | `57.10%` | `58.35%` | `+1.25%p` | promote | headline CAGR improved without extra drawdown |
| Full-period Sharpe | `1.6875` | `1.6888` | `+0.0013` | promote | Sharpe improved while MDD stayed flat |
| Walk-forward avg CAGR delta | `0.00%p` | `+1.29%p` | `+1.29%p` | promote | positive CAGR windows `3`, negative `0` |
| Cost latest CAGR delta | `0.00%p` | `+1.13%p` | `+1.13%p` | promote | still ahead at `75 bps` |
| Candidate avg monthly delta | `0.00%p` | `+0.097%p` | `+0.097%p` | promote | candidate keeps a positive average monthly edge over the retired strongest |
| Top-3 positive symbol share | `74.08%` | `74.08%` | `+0.00%p` | caution | concentration remains elevated and does not broaden the edge versus the retired strongest |
| Hard benchmark CAGR delta at `75 bps` | `+6.06%p` | `+7.19%p` | `+1.13%p` | promote | candidate stays further ahead of `12-1 full-universe top5` under high cost |
| Full-universe CAGR delta vs retired strongest | `0.00%p` | `+1.25%p` | `+1.25%p` | promote | strongest family edge improved where the branch family is actually strongest |
| Stock-only CAGR delta vs retired strongest | `0.00%p` | `0.00%p` | `0.00%p` | caution | branch remains mixed-universe; this promotion still does not create a stock-only edge |

## Interpretation

- this promotion was not based on headline CAGR alone
- the broader softer ranked-tail branch improved on every axis that mattered for promotion:
  - full-period quality
  - walk-forward
  - cost
  - hard benchmark defense
- the main things that did **not** change are:
  - this is still strongest as a mixed-universe aggressive branch
  - concentration is still compact-winner heavy in absolute terms
  - it should not be oversold as a universal stock-only model

## Verdict

- treat the broader ranked-tail branch as a real strongest-branch promotion
- use the ledger together with:
  - `docs/split_models_aggressive_branch_review.md`
  - `docs/split_models_branch_search_history.md`
- keep the caution language intact:
  - strongest aggressive branch
  - mixed-universe construction rule
  - still concentration-aware, not operational baseline material
