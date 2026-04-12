# EVENT_MOMENTUM_MAD_FIRST_RUN_SANITY_CHECK

## 1. What Actually Worked
- The first minimal backtest did run end-to-end and produced real artifacts.
- The event sheet was read, baskets were formed, momentum ranking was computed, and MAD-based sizing weights were written into the schedule.
- The event schedule is internally coherent at the event-date level:
  - 2 events
  - 5 rebalance checkpoints per event
  - 2 selected names per checkpoint
- Trade generation also ran and produced a non-empty trade log with 26 actions across 6 tickers.
- The schedule weights sum to 1.0 within each event checkpoint, so the event-level sizing logic itself is not obviously broken.

## 2. What Makes The Current Result Fragile
- The test uses only 2 events. That is far too small for any performance conclusion.
- The full backtest result is dominated by a very narrow thematic cluster: both events are semiconductor-related.
- The reported NAV window runs from 2022-08-11 to 2026-04-03, but the event schedule only runs through 2023-11-16. That means the portfolio appears to stay invested long after the explicit event window ends.
- Because of that persistence, the headline CAGR / Sharpe are not cleanly measuring short event trades; they are partly measuring a carried-forward residual portfolio.
- The first event’s selected names often have negative momentum scores, which means selection is relative inside a weak basket, not necessarily absolute strength.

## 3. Why Max Drawdown Is So Large
- Max drawdown is large mainly because the strategy appears to remain exposed well beyond the intended event holding windows.
- The worst drawdown occurs on 2024-12-04, long after the final scheduled event rebalance date of 2023-11-16.
- That strongly suggests the drawdown is not mainly an event-window drawdown; it is a residual post-event portfolio drawdown.
- The annualized volatility of about 50.6% is also too high for such a small event-driven sleeve unless exposure persistence is extending the holding period far beyond the intended design.

## 4. Whether Event Count Is Too Small To Matter
- Yes.
- Two events are enough to prove that the pipeline can run, but not enough to judge whether the strategy has a repeatable edge.
- With only 2 events, a single good or bad event can dominate the entire result.
- This is especially weak because both events are from the same broad semiconductor policy/trade theme.

## 5. Whether Trade Count Looks Reasonable
- The raw count of 26 actions is not itself unreasonable for 2 events with weekly rechecks and 2 selected names.
- The action pattern is consistent with the schedule:
  - 10 event-status checkpoints
  - 20 schedule rows
  - 26 trade actions after transitions
- So trade count is not the main problem.
- The main problem is that the resulting exposure seems to continue after the event schedule has already ended.

## 6. Likely Sources of Bias or Distortion
- Post-event exposure persistence beyond the final scheduled event date
- Very small event count
- Theme concentration in one industry cluster
- Manual event curation and manual basket definition
- Relative momentum selection inside a weak basket, which can still force the model to hold “least bad” names
- Next-day open was approximated using next-day close because only daily close data was used

## 7. What Must Be Checked Before Any Second Run
- Whether positions are explicitly flattened when the final event window ends
- Whether the reported NAV after 2023-11-16 is intended or accidental
- Whether the event sleeve should be 100% cash outside active event windows
- Whether the current summary metrics should be recomputed only over the active event-driven holding window
- Whether the same event/basket logic still behaves sensibly when the basket’s momentum scores are broadly negative

## 8. Supervisor Verdict
- The first run is useful as a pipeline proof, but not yet trustworthy as a strategy result.
- The main reason is not merely small sample size; it is that the current backtest appears to keep portfolio exposure alive beyond the explicit event schedule.
- Until that is verified and corrected if necessary, the current CAGR, Sharpe, and max drawdown should not be treated as decision-grade evidence for a second strategy judgment.
