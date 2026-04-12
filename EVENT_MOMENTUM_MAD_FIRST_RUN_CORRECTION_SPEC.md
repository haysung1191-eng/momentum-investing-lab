# EVENT_MOMENTUM_MAD_FIRST_RUN_CORRECTION_SPEC

## 1. What Must Be Fixed Immediately
- The backtest must explicitly flatten positions when the active event schedule ends.
- The reported NAV / CAGR / Sharpe / drawdown window must not continue as if positions are still active after the final scheduled event date.
- The second run must distinguish between:
  - active event-window exposure
  - out-of-event cash state
- The second run must also prevent a stock from being held simply because it ranks highest inside a uniformly weak basket.

## 2. Which Issues Are Structural vs Experimental
- Structural issues:
  - position persistence beyond the last event date
  - performance statistics being computed over a window distorted by that persistence
  - relative-only momentum selection allowing weak names to remain eligible inside a weak basket
- Experimental issues:
  - only 2 events
  - both events concentrated in one semiconductor-related theme
  - manual event and basket construction
- The structural issues must be fixed before any interpretation of strategy quality is attempted.
- The experimental issues do not need to be fixed yet for the second run, because the next run is still only a trustworthiness check.

## 3. Position-Lifecycle Correction
- The portfolio must be 100% cash outside active event windows.
- When an event reaches its final scheduled rebalance / holding date, all positions originating from that event must be closed immediately.
- If no active event remains, portfolio exposure must go to zero risk positions and 100% cash.
- The second run’s daily NAV must reflect only:
  - active event-driven positions during live event windows
  - cash outside those windows
- This is the highest-priority correction because it directly affects every reported performance metric.

## 4. Event-Scope Limitation
- Keep the second run limited to the same 2 events already used in the first run.
- Keep the same event sheet and the same candidate baskets.
- Do not add more events, even if sample size is small.
- The point of the second run is not broader validation; it is to remove the structural distortion from the first run while holding event scope constant.

## 5. Momentum-Strength Correction
- Keep the same relative momentum ranking method inside the basket.
- Add one minimum gate for the second run:
  - selected names must not only rank high within the basket
  - they must also have positive composite momentum score at the selection point
- If no basket names meet that condition at a rebalance check, the event sleeve should stay in cash for that checkpoint.
- This is not parameter tuning; it is a trustworthiness guard against holding “least bad” names when the full basket is weak.

## 6. What Must Not Be Changed Yet
- Do not add new event types
- Do not add new events
- Do not broaden the candidate universe
- Do not tune momentum lookbacks
- Do not tune MAD behavior
- Do not redesign transmission logic
- Do not generalize into a larger framework
- Do not change the weekly rebalance / 20-day maximum holding structure yet

## 7. The Single Smallest Safe Second Run
- Re-run the exact same 2-event backtest with only these corrections:
  - force event-window position closure at the final scheduled date
  - force 100% cash outside active event windows
  - require positive composite momentum score for selected names
- Then recompute the same summary metrics on that corrected run.
- No other changes should be introduced in the second run.

## 8. Supervisor Recommendation
- The second run should be treated as a correction run, not a new strategy test.
- Its purpose is to answer one question only:
  - does the minimal Event + Momentum + MAD pipeline still produce a coherent result after the most serious structural distortions are removed?
- Only after that correction run is clean should any discussion of adding events, expanding baskets, or evaluating edge quality continue.
