# 1. Strategy Objective

- Test whether the existing Global Flow Observer can be converted into a simple monthly allocation model that is strong enough to justify further research.
- This first test is not meant to maximize returns. It is meant to answer one narrow question: does the observer-derived regime mapping create a backtest that is at least credible enough to survive a first kill test.

# 2. Tradable Universe

Use only liquid US ETFs already close to the observer logic:

- SPY
- EFA
- EEM
- IEF
- TLT
- GLD
- PDBC
- BIL

Reason:
- These cover US equities, developed ex-US, emerging markets, intermediate and long duration, gold, commodities, and cash.
- This is enough to express the current observer regimes without adding sector or credit complexity yet.

# 3. Regime-To-Allocation Mapping

Use the existing observer regime label only. Do not change regime logic.

- Risk-On
  - 40% SPY
  - 20% EFA
  - 20% EEM
  - 10% GLD
  - 10% PDBC

- Risk-Off
  - 50% IEF
  - 30% TLT
  - 20% BIL

- Inflation Tilt
  - 35% GLD
  - 35% PDBC
  - 15% EEM
  - 15% IEF

- Duration Bid
  - 40% TLT
  - 40% IEF
  - 20% BIL

- Mixed
  - 20% SPY
  - 10% EFA
  - 10% EEM
  - 20% IEF
  - 10% TLT
  - 15% GLD
  - 15% PDBC

# 4. Rebalance Timing

- Frequency: monthly only
- Signal date: last trading day of each completed month
- Execution date assumption: next trading day
- No intramonth changes

# 5. Entry / Exit Logic

- On each monthly signal date, read the observer regime for that month.
- On the next trading day, rebalance fully into the fixed allocation mapped to that regime.
- Exit from prior holdings occurs only through the monthly rebalance into the new mapped allocation.
- No discretionary override.

# 6. Cash / Defensive Behavior

- BIL is the only cash-equivalent sleeve in this first test.
- Cash appears only where the fixed regime mapping explicitly assigns BIL weight.
- There is no separate tactical stop rule in this first backtest.

# 7. Position Sizing Rule

- Use the fixed weights defined by the regime mapping.
- Fully invested at each rebalance, except for the explicit BIL sleeve.
- No leverage.
- No volatility targeting.
- No optimization.
- No transaction-cost-aware resizing beyond standard backtest cost application.

# 8. Evaluation Metrics

Minimum required metrics:

- CAGR
- Max drawdown
- Annualized volatility
- Sharpe
- Final total return
- Turnover
- Monthly regime counts
- Benchmark comparison versus SPY buy-and-hold over the same period

# 9. Kill Rule

Kill this first model immediately if either condition is true:

- net Sharpe <= 0.5
- or net CAGR materially trails SPY while not delivering a clearly better drawdown profile

Operational interpretation:
- This branch should survive only if it shows at least a plausible tradeoff between return and drawdown.
- A merely descriptive regime model with weak investable performance should be stopped early.

# 10. What The First Backtest Will Not Attempt

- No parameter search
- No alternate regime logic
- No sector rotation
- No credit sleeve expansion
- No stock selection
- No tactical momentum overlay on top of regime mapping
- No intramonth trading
- No execution automation
- No tax modeling
- No attempt to prove the final strategy design

This first backtest is only a falsifiable test of whether the existing observer can support a simple investable allocation rule at all.
