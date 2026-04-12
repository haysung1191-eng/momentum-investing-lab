# EVENT_MOMENTUM_MAD_MINIMAL_BACKTEST_SPEC

## 1. First Test Market
- Korea equities only.
- Daily bar backtest only.
- First test period: use the maximum period supported by clean daily price history and event timestamps, but require the same point-in-time treatment for every event instance.

## 2. First Event Types To Include
- Government policy / regulation announcements affecting a named industry
- Tariff / trade policy announcements affecting export-linked or input-cost-sensitive industries
- Commodity shock events affecting clearly linked producer / consumer industry groups

## 3. Event Detection Source
- Use a manually curated event sheet as the first source.
- Each event row must include at minimum:
  - event_id
  - event_date
  - event_type
  - event_title
  - short event description
  - affected industry or theme
- The event sheet must be created only from sources that were public on the event date.
- No inferred event dates and no retrospective relabeling after price moves.

## 4. Candidate Universe Definition
- Use a fixed Korea stock universe with:
  - common stocks only
  - sufficient daily price history
  - minimum liquidity filter applied consistently across the test window
- For the first test, candidate baskets drawn from that universe should target 5 to 20 names per event.
- Every included stock must have a prewritten event linkage label:
  - direct beneficiary
  - indirect beneficiary
  - likely loser
- First minimal test uses beneficiary-side names only.

## 5. Transmission Mapping Rule
- Each event must be mapped to 1 to 3 transmission variables before any backtest entry is allowed.
- Allowed transmission variable types in the first test:
  - relevant commodity price
  - KRW FX level or relevant external FX level
  - sector index / industry index move
  - upstream/downstream spread proxy if available
- Mapping rule:
  - each transmission variable must have a written reason linking event to basket economics
  - if no clear transmission mapping can be written, the event is excluded from the test

## 6. Momentum Measurement Rule
- Momentum is measured only within the event basket, not versus the entire market.
- Use trailing daily total-return proxies over:
  - 20 trading days
  - 60 trading days
  - 120 trading days
- Compute a composite momentum rank from those three horizons using fixed equal weight.
- Eligible names for entry are the top-ranked names inside the basket.
- First test selection rule:
  - choose the top 30% of names in the basket, rounded down but never fewer than 1 name

## 7. MAD Measurement Rule
- MAD is measured cross-sectionally within the event basket.
- Use median absolute deviation of standardized recent return behavior across basket members.
- First test purpose of MAD:
  - adjust size down for unstable outliers
  - not act as the main selection rule
- First test default:
  - no hard rejection from MAD unless the name has invalid or unusable data

## 8. Entry Timing Rule
- Entry evaluation starts on the first market close after the event date is public.
- On that evaluation date:
  - confirm the event is valid
  - build the candidate basket using only information available then
  - compute basket-relative momentum ranking
  - select the top momentum names
- First test assumes entry at next trading day open after the evaluation close.

## 9. Exit Timing Rule
- Exit at the earliest of:
  - fixed maximum holding window expires
  - the name falls out of the selected top momentum group at the scheduled rebalance check
  - transmission mapping is invalidated by a defined opposing move
- First minimal holding design:
  - weekly rebalance check
  - maximum holding window: 20 trading days

## 10. Position Sizing Rule
- Start from equal weight across selected names for an event.
- Apply MAD-based scaling:
  - lower MAD names receive modestly larger weight
  - higher MAD names receive modestly smaller weight
- Normalize weights back to the event sleeve total.
- The first test must also compute an equal-weight selected-basket baseline so MAD contribution can be compared directly.

## 11. Max Concurrent Positions
- Max concurrent positions across the full strategy: 10 names.
- If overlapping active events produce more than 10 names:
  - first rank by event recency
  - then by within-basket momentum rank
  - then cap at 10 without discretionary override

## 12. No-Trade Conditions
- Do not trade an event if:
  - event timestamp is unclear
  - basket has fewer than 3 valid candidate names
  - required transmission mapping is unclear
  - required momentum lookback data is missing
  - MAD cannot be computed due to unusable data
  - event sheet evidence is not point-in-time defensible

## 13. Evaluation Metrics
- Event count tested
- Trade count
- Hit rate
- CAGR
- Max drawdown
- Sharpe
- Average holding period
- Average basket size
- Selected-name return vs raw full-basket return
- MAD-sized selected basket vs equal-weight selected basket

## 14. What This First Backtest Will Not Attempt
- No automated event extraction from unstructured text
- No intraday timing
- No short-selling sleeve
- No adaptive parameter tuning
- No broader multi-market rollout
- No proof of production readiness
- No claim that the full event strategy family is validated from this first test alone
