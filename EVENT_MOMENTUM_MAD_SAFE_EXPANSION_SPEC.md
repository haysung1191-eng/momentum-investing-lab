# EVENT_MOMENTUM_MAD_SAFE_EXPANSION_SPEC

## 1. Why A Third Run Is Justified
- The correction run removed the most serious structural distortions from the first run.
- The current result is still too small to judge because only 2 events were tested.
- A third run is justified only to answer one narrow question:
  - does the corrected Event + Momentum + MAD pipeline still behave coherently when the event count is no longer trivial?
- This is not a performance-improvement step.

## 2. What Must Stay Frozen
- Korea equities only
- Daily bar implementation only
- Same event -> transmission mapping -> candidate basket -> momentum -> MAD pipeline
- Same event sheet structure
- Same candidate basket construction logic
- Same momentum measurement rule:
  - 20 / 60 / 120 trading-day composite
- Same positive composite momentum gate
- Same MAD sizing method
- Same weekly rebalance check
- Same 20-trading-day maximum holding window
- Same max concurrent positions rule

## 3. Target Event Count Range
- Third run target: 8 to 15 events.
- Fewer than 8 is still too close to anecdotal sample size.
- More than 15 is not needed for the next run and increases the risk of uncontrolled scope expansion.

## 4. Event Diversity Requirement
- The third run must not be dominated by one single industry theme.
- At minimum, the added events should span more than one causal bucket.
- Practical minimum diversity rule:
  - no more than 50% of the full third-run event set may come from one narrow industry cluster
- The purpose is not broad coverage; it is to avoid repeating the “two semiconductor events only” limitation.

## 5. Allowed Event Types For Expansion
- policy / regulation announcements
- tariff / trade policy announcements
- commodity shock events
- No other event categories should be introduced in the third run.

## 6. Event Selection Rules
- Every added event must satisfy all of the original minimal-spec requirements:
  - clear public date
  - explicit event title
  - explicit affected theme
  - 1 to 3 explicit transmission variables
  - explicit candidate basket with written rationale
- Added events must be selected before looking at their realized basket performance.
- Event selection must favor clarity and defensibility over quantity.
- If an event is difficult to explain causally, exclude it.

## 7. What Must Be Excluded
- Any event with unclear timing
- Any event whose affected basket cannot be defended in writing
- Any event that requires a new strategy rule to handle
- Any event that would require broadening the stock universe redesign
- Any event that depends on a new momentum formula or new MAD formula
- Any event included only because it “looks good in hindsight”

## 8. What Would Count As A Meaningful Third Run
- The run completes with a materially larger event count than the correction run.
- The corrected lifecycle behavior remains intact:
  - no hidden post-event exposure persistence
  - cash outside active windows
- The pipeline produces a coherent mix of:
  - tradable events
  - cash checkpoints when momentum is not strong enough
- The result should be judged meaningful if it shows that the corrected structure still functions sensibly under a nontrivial event sample, regardless of whether headline performance improves.

## 9. Supervisor Verdict
- Proceed to a third run only as a controlled event-sample expansion.
- Keep the structure frozen.
- Increase event count enough to test stability, but not enough to turn the exercise into a redesign.
