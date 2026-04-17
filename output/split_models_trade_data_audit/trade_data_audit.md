# Split Models Trade And Data Audit

## Today Work

- tradeoff frontier refresh
- quality-vs-headline refresh
- nightly safe summary
- overnight guardrail
- quality recipient family review
- promotion defense refresh
- dead family ledger refresh
- redistribution family saturation review
- tail-rescue saturation fix
- many inline genuinely-different family validations

## Price Data Source

- US stocks: `data/prices_us_stock_sp100_pitwiki/stock/*.csv.gz`
- US ETFs: `data/prices_us_etf_core/etf/*.csv.gz`
- KR stocks and ETFs: `data/prices_operating_institutional_v1/{stock,etf}/*.csv.gz`
- KR stock flows: `data/flows_operating_institutional_v1/stock/*.csv.gz`

## Model Trade Snapshot

- strongest: `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
  - latest signal date: `2026-01-30`
  - latest next date: `2026-02-27`
  - entered: `0000J0, CAT, GILD, GS, JNJ, LMT`
  - exited: `360750, BIIB, C, LLY, LRCX, MU`
  - holding: `KR:069500` `069500` weight `0.4979` mom `0.1639` flow `na`
  - holding: `KR:0000J0` `0000J0` weight `0.4979` mom `0.1297` flow `na`
  - holding: `US:LMT` `Lockheed Martin` weight `0.0500` mom `0.1003` flow `0.305742`
  - holding: `US:CAT` `Caterpillar` weight `0.0393` mom `0.0893` flow `0.158032`
  - holding: `US:JNJ` `Johnson & Johnson` weight `0.0348` mom `0.0792` flow `0.174038`
- broader: `hybrid_top2_plus_third00125`
  - latest signal date: `2026-01-30`
  - latest next date: `2026-02-27`
  - entered: `0000J0, CAT, GILD, GS, JNJ, LMT`
  - exited: `360750, BIIB, C, LLY, LRCX, MU`
  - holding: `KR:069500` `069500` weight `0.4974` mom `0.1639` flow `na`
  - holding: `KR:0000J0` `0000J0` weight `0.4974` mom `0.1297` flow `na`
  - holding: `US:LMT` `Lockheed Martin` weight `0.0512` mom `0.1003` flow `0.305742`
  - holding: `US:CAT` `Caterpillar` weight `0.0392` mom `0.0893` flow `0.158032`
  - holding: `US:JNJ` `Johnson & Johnson` weight `0.0348` mom `0.0792` flow `0.174038`
- quality: `bonus_recipient_top1_third_85_15`
  - latest signal date: `2026-01-30`
  - latest next date: `2026-02-27`
  - entered: `0000J0, CAT, GILD, GS, JNJ, LMT`
  - exited: `360750, BIIB, C, LLY, LRCX, MU`
  - holding: `KR:069500` `069500` weight `0.5609` mom `0.1639` flow `na`
  - holding: `KR:0000J0` `0000J0` weight `0.4079` mom `0.1297` flow `na`
  - holding: `US:LMT` `Lockheed Martin` weight `0.0770` mom `0.1003` flow `0.305742`
  - holding: `US:CAT` `Caterpillar` weight `0.0393` mom `0.0893` flow `0.158032`
  - holding: `US:JNJ` `Johnson & Johnson` weight `0.0348` mom `0.0792` flow `0.174038`
- headline: `tail_skip_entry_flowweakest_new_bottom4_top25_mid75`
  - latest signal date: `2026-01-30`
  - latest next date: `2026-02-27`
  - entered: `0000J0, CAT, GS, JNJ, LMT`
  - exited: `360750, BIIB, LLY, LRCX, MU`
  - holding: `KR:069500` `069500` weight `0.4253` mom `0.1639` flow `na`
  - holding: `KR:0000J0` `0000J0` weight `0.4253` mom `0.1297` flow `na`
  - holding: `US:LMT` `Lockheed Martin` weight `0.0490` mom `0.1003` flow `0.305742`
  - holding: `US:CAT` `Caterpillar` weight `0.0400` mom `0.0893` flow `0.158032`
  - holding: `US:JNJ` `Johnson & Johnson` weight `0.0362` mom `0.0792` flow `0.174038`
- defensive_weighting: `regime_weight_defensive_if_top2flowsoft`
  - latest signal date: `2026-01-30`
  - latest next date: `2026-02-27`
  - entered: `0000J0, CAT, GILD, GS, JNJ, LMT`
  - exited: `360750, BIIB, C, LLY, LRCX, MU`
  - holding: `KR:069500` `069500` weight `0.4008` mom `0.1639` flow `0.0`
  - holding: `KR:0000J0` `0000J0` weight `0.4008` mom `0.1297` flow `0.0`
  - holding: `US:LMT` `Lockheed Martin` weight `0.0539` mom `0.1003` flow `0.305742`
  - holding: `US:CAT` `Caterpillar` weight `0.0423` mom `0.0893` flow `0.158032`
  - holding: `US:JNJ` `Johnson & Johnson` weight `0.0376` mom `0.0792` flow `0.174038`
- stronger_but_more_fragile: `multi_step_confirm_top1_flowtop2`
  - latest signal date: `2026-01-30`
  - latest next date: `2026-02-27`
  - entered: `0000J0, CAT, GILD, GS, JNJ, LMT`
  - exited: `360750, BIIB, C, LLY, LRCX, MU`
  - holding: `KR:0000J0` `0000J0` weight `0.4474` mom `0.1297` flow `na`
  - holding: `KR:069500` `069500` weight `0.3965` mom `0.1639` flow `na`
  - holding: `US:LMT` `Lockheed Martin` weight `0.0424` mom `0.1003` flow `0.305742`
  - holding: `US:CAT` `Caterpillar` weight `0.0333` mom `0.0893` flow `0.158032`
  - holding: `US:JNJ` `Johnson & Johnson` weight `0.0295` mom `0.0792` flow `0.174038`
- redistribution: `tail_release_top50_mid50`
  - latest signal date: `2026-01-30`
  - latest next date: `2026-02-27`
  - entered: `0000J0, CAT, GILD, GS, JNJ, LMT`
  - exited: `360750, BIIB, C, LLY, LRCX, MU`
  - holding: `KR:069500` `069500` weight `0.4778` mom `0.1639` flow `na`
  - holding: `KR:0000J0` `0000J0` weight `0.4778` mom `0.1297` flow `na`
  - holding: `US:LMT` `Lockheed Martin` weight `0.0157` mom `0.1003` flow `0.305742`
  - holding: `US:CAT` `Caterpillar` weight `0.0097` mom `0.0893` flow `0.158032`
  - holding: `US:JNJ` `Johnson & Johnson` weight `0.0076` mom `0.0792` flow `0.174038`

## Price File Audit

- `KR:069500` `069500`
  - path: `C:\AI\momentum\data\prices_operating_institutional_v1\etf\069500.csv.gz`
  - exists: `True`
  - rows: `2001`
  - range: `2018-02-12 -> 2026-04-10`
  - nonpositive close rows: `0`
  - duplicate date rows: `0`
- `KR:0000J0` `0000J0`
  - path: `C:\AI\momentum\data\prices_operating_institutional_v1\etf\0000J0.csv.gz`
  - exists: `True`
  - rows: `313`
  - range: `2024-12-24 -> 2026-04-10`
  - nonpositive close rows: `0`
  - duplicate date rows: `0`
- `US:LMT` `Lockheed Martin`
  - path: `C:\AI\momentum\data\prices_us_stock_sp100_pitwiki\stock\LMT.csv.gz`
  - exists: `True`
  - rows: `2825`
  - range: `2015-01-02 -> 2026-03-27`
  - nonpositive close rows: `0`
  - duplicate date rows: `0`
- `US:CAT` `Caterpillar`
  - path: `C:\AI\momentum\data\prices_us_stock_sp100_pitwiki\stock\CAT.csv.gz`
  - exists: `True`
  - rows: `2825`
  - range: `2015-01-02 -> 2026-03-27`
  - nonpositive close rows: `0`
  - duplicate date rows: `0`
- `US:JNJ` `Johnson & Johnson`
  - path: `C:\AI\momentum\data\prices_us_stock_sp100_pitwiki\stock\JNJ.csv.gz`
  - exists: `True`
  - rows: `2825`
  - range: `2015-01-02 -> 2026-03-27`
  - nonpositive close rows: `0`
  - duplicate date rows: `0`

## Verdict

- future review should include both current holdings and entered/exited symbols, not just performance deltas
- backtest price data is local cached csv.gz data, so trust should be based on file-level auditability rather than assumption
