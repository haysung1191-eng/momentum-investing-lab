# Split Models Promotion Defense Refresh

## Purpose

- freeze the current strongest after another batch of family exploration
- make it obvious why the strongest still stays after many near-miss tests

## Current Truth

- strongest: `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
  - CAGR `63.16%`
  - MDD `-29.27%`
  - Sharpe `1.6892`
  - Annual turnover `15.32`
- broader challenger: `hybrid_top2_plus_third00125`
  - CAGR `63.12%`
  - Sharpe `1.6895`
  - walk-forward `2 positive / 2 negative`
  - takeaway `best broader-but-weaker point`
- quality near-miss: `bonus_recipient_top1_third_85_15`
  - CAGR `65.43%`
  - Sharpe `1.6927`
  - walk-forward `3 positive / 1 negative`
  - takeaway `best blended-quality extension, but drawdown and walk-forward Sharpe still fail promotion grade`
- headline near-miss: `tail_skip_entry_flowweakest_new_bottom4_top25_mid75`
  - CAGR `63.21%`
  - MDD `-28.77%`
  - walk-forward `3 positive / 1 negative`
  - takeaway `best headline extension, but Sharpe still stays too weak`
- stronger-but-lower-quality near-miss: `tail_release_top50_mid50`
  - CAGR `76.47%`
  - MDD `-34.64%`
  - walk-forward `4 positive / 0 negative`
  - takeaway `best redistribution contender; headline and Sharpe both improve, but drawdown still worsens too much for promotion`

## Recent Failed Families

- quality-headline hybrid: `hybrid_quality85_skipentry_top25_mid75`
  - strongest signal: `+1.56%p CAGR and +0.25%p MDD`
  - failure reason: `Sharpe delta -0.0394 and walk-forward Sharpe stayed clearly negative`
- risk-on exposure: `risk_on_exposure_106`
  - strongest signal: `no candidate beat strongest headline`
  - failure reason: `all scanned points were weaker on CAGR, walk-forward, and cost together`
- risk-off tightening: `risk_off_tighten_sector075`
  - strongest signal: `+0.0150 Sharpe`
  - failure reason: `CAGR delta -1.53%p with 1 positive / 3 negative walk-forward windows`
- entry filter: `entry_filter_soft_r1m20_pen50`
  - strongest signal: `+0.50%p MDD improvement`
  - failure reason: `CAGR delta -0.73%p and cost-adjusted Sharpe stayed negative`
- hold buffer: `hold_buffer1 / hold_buffer2`
  - strongest signal: `no-op`
  - failure reason: `identical to strongest; no research value in this branch family`
- position cap: `position_cap_us4`
  - strongest signal: `+2.40%p MDD improvement`
  - failure reason: `CAGR delta -22.78%p and walk-forward 0 positive / 4 negative`
- sector cap relaxation: `sector_cap3`
  - strongest signal: `+2.18%p MDD improvement`
  - failure reason: `CAGR delta -6.07%p and walk-forward 0 positive / 4 negative`
- flow filter: `flow_filter_uscap035`
  - strongest signal: `none`
  - failure reason: `CAGR delta -33.00%p and Sharpe delta -0.3538`
- soft blacklist: `soft_blacklist_top3_pen85`
  - strongest signal: `+0.20%p MDD improvement`
  - failure reason: `CAGR delta -2.05%p and Sharpe delta -0.0824`
- dynamic bonus sizing: `dynamic_bonus_tight14_if_top42`
  - strongest signal: `slightly lower turnover`
  - failure reason: `CAGR delta -1.51%p and fragility worsened`
- aggressive redistribution: `tail_release_top50_mid50`
  - strongest signal: `+13.31%p CAGR, +0.0075 Sharpe, and 4 positive / 0 negative walk-forward windows`
  - failure reason: `MDD delta -5.37%p still leaves it outside promotion grade despite the much stronger headline`

## Verdict

- keep the current strongest; recent search widened the near-miss map but did not produce a new promotion-grade stronger branch
- recent search mostly improved explanation quality, not mainline promotion quality
- keep future search focused on genuinely different families instead of re-litigating dead axes
