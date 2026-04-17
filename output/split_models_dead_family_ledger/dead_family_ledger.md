# Split Models Dead Family Ledger

## Purpose

- record which family axes are dead or no-op under the current strongest
- reduce repeated overnight search on already disproven branches

## Current strongest

- `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`

## Ledger

- quality-headline hybrid: `dead`
  - best tested point: `hybrid_quality85_skipentry_top25_mid75`
  - strongest signal: `+1.56%p CAGR, +0.25%p MDD, walk-forward 4 positive / 0 negative`
  - kill reason: `Sharpe delta -0.0394 and both walk-forward/cost Sharpe stayed clearly negative`
  - retry rule: `do not retry unless the hybrid changes a different robustness axis than recipient plus skip-entry mixing`
- risk-on exposure: `dead`
  - best tested point: `risk_on_exposure_106`
  - strongest signal: `none; scanned points stayed weaker than strongest`
  - kill reason: `CAGR, walk-forward, and cost all weakened together`
  - retry rule: `do not retry simple exposure bumps around 1.02-1.06`
- risk-off tightening: `dead`
  - best tested point: `risk_off_tighten_sector075`
  - strongest signal: `+0.0150 Sharpe`
  - kill reason: `headline strength collapsed; CAGR delta -1.53%p with 1 positive / 3 negative walk-forward windows`
  - retry rule: `do not retry tighter sector risk-off without a separate offsetting alpha source`
- entry filter: `dead`
  - best tested point: `entry_filter_soft_r1m20_pen50`
  - strongest signal: `+0.50%p MDD improvement`
  - kill reason: `CAGR and Sharpe both weakened and walk-forward stayed 2 positive / 2 negative`
  - retry rule: `do not retry simple entrant overheat penalties around soft r1m 0.20`
- hold buffer: `no-op`
  - best tested point: `hold_buffer1 / hold_buffer2`
  - strongest signal: `identical to strongest`
  - kill reason: `selection did not change at all`
  - retry rule: `do not retry hold-buffer variants unless the base selection logic itself changes`
- position cap: `dead`
  - best tested point: `position_cap_us4`
  - strongest signal: `+2.40%p MDD improvement and lower turnover`
  - kill reason: `CAGR delta -22.78%p and walk-forward 0 positive / 4 negative`
  - retry rule: `do not retry harder US cap reductions around 5 -> 4`
- sector cap relaxation: `dead`
  - best tested point: `sector_cap3`
  - strongest signal: `+2.18%p MDD improvement and lower turnover`
  - kill reason: `CAGR delta -6.07%p and walk-forward 0 positive / 4 negative`
  - retry rule: `do not retry looser sector cap around 2 -> 3`
- flow filter: `dead`
  - best tested point: `flow_filter_uscap035`
  - strongest signal: `none`
  - kill reason: `CAGR delta -33.00%p, Sharpe delta -0.3538, cost and residual both collapsed`
  - retry rule: `do not retry simple US flow caps near 0.35`
- soft blacklist: `dead`
  - best tested point: `soft_blacklist_top3_pen85`
  - strongest signal: `+0.20%p MDD improvement and lower winner dependence`
  - kill reason: `CAGR delta -2.05%p and Sharpe delta -0.0824`
  - retry rule: `do not retry direct soft penalties on PLTR/NVDA/MU without a compensating new alpha source`
- dynamic bonus sizing: `dead`
  - best tested point: `dynamic_bonus_tight14_if_top42`
  - strongest signal: `slightly lower turnover`
  - kill reason: `CAGR delta -1.51%p and fragility actually worsened`
  - retry rule: `do not retry simple bonus-tightening rules based only on top2 concentration`
- KR unknown exclusion: `no-op`
  - best tested point: `exclude_kr_unknown_strongest`
  - strongest signal: `identical to strongest`
  - kill reason: `selection did not change at all`
  - retry rule: `do not retry this family unless KR unknown names start entering the strongest book`
- liquidity gate: `dead`
  - best tested point: `liquidity_gate_relvol105`
  - strongest signal: `none`
  - kill reason: `CAGR delta -42.03%p, MDD got worse, Sharpe collapsed, turnover rose`
  - retry rule: `do not retry min_rel_volume around 1.05 or higher as a mainline branch search axis`

## Verdict

- recent search has enough evidence to stop repeating these families under the current strongest
- future search should favor genuinely different families instead of recycling these axes
