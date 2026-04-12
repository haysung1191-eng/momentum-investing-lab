# EVENT_MOMENTUM_MAD_STRATEGY

## 1. Strategy Objective
- Build a causal event-driven stock strategy that starts from real-world events, maps those events into affected stock baskets, and then uses momentum to decide which names are actually working in price.
- Use transmission variables to explain why the event should matter economically.
- Use MAD mainly to scale position size according to cross-sectional dispersion and instability, not to automatically reject names by default.
- The goal is to trade only when an event has a plausible transmission path and market confirmation exists in price.

## 2. What Counts as an Event
- An event is a discrete, time-stamped development that can plausibly affect a defined set of stocks through an identifiable economic channel.
- Valid event categories for the first version:
  - policy / regulation change
  - tariff / trade action
  - commodity supply shock
  - major fiscal / budget announcement
  - large sector-specific rule change
  - sudden demand / capex signal affecting an identifiable industry
- An event is not valid if:
  - timing is unclear
  - affected basket is unclear
  - transmission path is unclear
  - it is only a narrative without a defined mechanism

## 3. Transmission Variables
- Transmission variables are the small set of measurable state variables that explain why the event should affect the basket.
- They are not entry triggers by themselves; they are explanatory and validation variables.
- Minimum transmission variable types:
  - direct price-linked variable:
    - commodity price
    - FX level
    - rate level
  - event-linked sector variable:
    - relevant sector ETF / index performance
    - upstream/downstream spread
  - sensitivity descriptor:
    - whether the candidate is beneficiary, neutral, or likely loser from the event
- First implementation rule:
  - every event must be attached to 1 to 3 explicit transmission variables
  - if no transmission variables can be named clearly, the event should not enter the strategy

## 4. Candidate Basket Construction
- Start with the event.
- Define an event-specific candidate basket of stocks that are plausibly connected to that event through revenue, cost, demand, inventory, capex, regulation, or supply-chain exposure.
- Basket construction should be explicit and small enough to defend.
- First version rules:
  - basket size target: 5 to 20 names
  - each stock must have a stated relationship to the event:
    - direct beneficiary
    - indirect beneficiary
    - neutral / uncertain
    - likely loser
- The tradable candidate set for the first version should normally use only beneficiary-side names unless the event explicitly supports a two-sided structure.

## 5. Momentum Selection Rule
- Momentum is the actual market-confirmation layer.
- The event creates the basket; momentum decides which candidates are strong enough to trade.
- First version rule:
  - compute trailing relative momentum across the event basket
  - use medium-horizon momentum, not very short-term noise
  - minimum practical horizons:
    - 1 month
    - 3 month
    - 6 month
- Select only the top-ranked names inside the event basket.
- Momentum does:
  - choose which event-linked names are actually working
  - reduce narrative-only picks
  - concentrate the basket into names with real price confirmation
- Momentum does not:
  - explain the event
  - replace event logic
  - replace risk sizing

## 6. MAD Usage Rule
- MAD is a risk-sizing layer based on dispersion / instability, not the core alpha decision layer.
- MAD should not automatically hard-reject a name by default.
- First version rule:
  - use MAD to reduce position size when a stock’s behavior is too noisy or unstable relative to its event basket
  - lower MAD = larger allowed size
  - higher MAD = smaller allowed size
- MAD may hard-reject only in exceptional cases:
  - missing / corrupted data
  - extreme outlier behavior that makes sizing meaningless
- Default interpretation:
  - momentum says whether to include
  - MAD says how large to size

## 7. Entry Rule
- Entry requires all three layers to line up:
  - a valid event exists
  - a candidate basket has been constructed with explicit transmission logic
  - the stock ranks high enough on momentum inside that basket
- First version entry rule:
  - open a position only in names that are in the selected top momentum group within the event basket
  - use the current active event window only
  - do not enter names solely because they are low-MAD

## 8. Exit Rule
- Exit when the event thesis is no longer active or the stock loses market confirmation.
- First version exit triggers:
  - the event window expires
  - the stock falls out of the selected momentum group
  - the transmission variables move clearly against the thesis
  - the stock becomes too unstable for sensible sizing under the MAD layer
- Exit should be rule-based, not narrative-discretionary.

## 9. Position Sizing Rule
- Position sizing starts from equal-weight among selected momentum names, then adjusts by MAD.
- First version rule:
  - select the final tradable set from momentum ranking
  - assign a base equal weight
  - scale weights down for higher-MAD names
  - scale weights up modestly for lower-MAD names
  - normalize back to the portfolio weight budget
- Position sizing should remain bounded:
  - no single name should dominate just because its MAD is low
  - MAD is an adjustment, not a full optimizer

## 10. When Not To Trade
- Do not trade when:
  - the event is not clearly time-stamped
  - the transmission path is unclear
  - the candidate basket is weak or arbitrary
  - momentum confirmation is absent across the basket
  - data needed for event timing, momentum ranking, or MAD sizing is missing or unreliable
  - the basket has too few valid names for meaningful selection

## 11. Failure Modes
- Wrong event attribution:
  - the event is real, but the basket is not truly exposed
- Narrative without price confirmation:
  - the story sounds right, but momentum does not confirm it
- Momentum crowding:
  - event-linked names have already moved too far before entry
- Basket contamination:
  - too many weakly related names dilute the event signal
- MAD misuse:
  - using MAD as a hidden rejection rule instead of a sizing discipline
- Transmission mismatch:
  - chosen transmission variables do not actually explain the realized move

## 12. First Minimal Backtest Specification
- Universe:
  - a defined stock universe with sufficient liquidity and clean daily price history
- Test unit:
  - event instances, each with:
    - event date
    - event category
    - transmission variables
    - candidate basket
- Process:
  - define the event basket as of the event date
  - compute momentum ranking only with information available at that time
  - select the top momentum names from the basket
  - size positions using the MAD adjustment rule
  - hold until the defined exit rule is triggered
- Minimum outputs:
  - event-by-event return summary
  - basket hit rate
  - selected-name hit rate
  - contribution of momentum selection vs raw basket
  - contribution of MAD sizing vs equal-weight selected basket
  - turnover
  - max drawdown
  - Sharpe
- First validation question:
  - does event + momentum produce better results than just holding the full raw candidate basket, and does MAD sizing improve risk control without becoming a hidden rejection filter?
