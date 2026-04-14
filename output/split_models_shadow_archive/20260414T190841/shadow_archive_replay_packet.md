# Split Models Archive Replay Packet

- archive run id: `20260414T190841`
- baseline variant: `rule_breadth_it_us5_cap`
- live readiness: `GO`
- health verdict: `PASS`
- drift verdict: `PASS`
- operator gate verdict: `PASS`
- archive consistency verdict: `PASS`
- archive stability verdict: `PASS`
- archive timeline verdict: `PASS`
- current holdings: `8`
- dominant sector: `Industrials`
- transition turnover: `11.11%`

## Replay Context
- in latest timeline window: `True`
- timeline rank: `2` of `8`
- prior run id: `20260414T180315`
- holdings change vs prior: `0`
- dominant sector changed vs prior: `False`
- readiness changed vs prior: `False`
- operator gate changed vs prior: `False`
- next run id: `20260414T191107`

## Archived Operator Packet
# Split Models Live Transition Packet

- baseline variant: `rule_breadth_it_us5_cap`
- live readiness verdict: `GO`
- signal date: `2026-01-30`
- current holdings: `8`
- current dominant sector: `Industrials`
- transition weight turnover: `11.11%`
- operator gate verdict: `PASS`
- archive consistency verdict: `PASS`
- archive stability verdict: `PASS`
- archive stability window: `5` runs

## Readiness checks
- HealthPass: `PASS` (value=PASS, threshold=PASS)
- DriftPass: `PASS` (value=PASS, threshold=PASS)
- MinHoldings: `PASS` (value=8, threshold=>=4)
- Top1Weight: `PASS` (value=0.125, threshold=<=0.25)
- Top3Weight: `PASS` (value=0.375, threshold=<=0.60)
- RecentTurnover: `PASS` (value=0.9612103174603175, threshold=<=1.50)
- TransitionTurnover: `PASS` (value=0.11111111111111113, threshold=<=0.20)

## Market execution summary
- KR BUY: `3` orders, `4.17%` gross weight, `4,166,667` gross notional
- US BUY: `5` orders, `6.94%` gross weight, `6,944,444` gross notional
- US SELL: `1` orders, `11.11%` gross weight, `11,111,111` gross notional

## Actionable orders
- SELL `GILD` (US / Health Care): `-11.11%`
- BUY `0000J0` (KR / ETF): `1.39%`
- BUY `0000Z0` (KR / ETF): `1.39%`
- BUY `069500` (KR / ETF): `1.39%`
- BUY `CAT` (US / Industrials): `1.39%`
- BUY `FDX` (US / Industrials): `1.39%`
- BUY `GEV` (US / Industrials): `1.39%`
- BUY `JNJ` (US / Health Care): `1.39%`
- BUY `LMT` (US / Industrials): `1.39%`

## Operator note
- If live capital is still on `rule_breadth_it_risk_off`, this packet is the single-file handoff for transition into `rule_breadth_it_us5_cap`.
