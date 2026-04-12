# 1. Purpose

- Test whether the first observer-derived model only passed because of one specific hand-written regime-to-allocation mapping.
- This is not a new strategy branch.
- This is a correction-style sanity check on the current mapping layer only.

# 2. What Must Stay Frozen

- The Global Flow Observer regime logic
- The fixed 8-ETF tradable universe
- Monthly signal timing
- Next-trading-day execution assumption
- Benchmark = SPY buy-and-hold
- Cost assumption = same as the first run unless otherwise stated in the runner
- Kill rule = unchanged

# 3. Single Change Allowed

- Only the regime-to-allocation mapping may be changed.
- The change must be conservative and compressive, not more aggressive.
- No new assets, no leverage, no tactical overlay, no momentum overlay.

# 4. Correction Mapping Rule

Replace the first-run mapping with a more conservative and less expressive mapping:

- Risk-On
  - 35% SPY
  - 15% EFA
  - 15% EEM
  - 20% IEF
  - 5% GLD
  - 5% PDBC
  - 5% BIL

- Risk-Off
  - 45% IEF
  - 25% TLT
  - 30% BIL

- Inflation Tilt
  - 25% GLD
  - 25% PDBC
  - 10% EEM
  - 20% IEF
  - 20% BIL

- Duration Bid
  - 35% TLT
  - 35% IEF
  - 30% BIL

- Mixed
  - 15% SPY
  - 10% EFA
  - 5% EEM
  - 25% IEF
  - 10% TLT
  - 10% GLD
  - 10% PDBC
  - 15% BIL

# 5. Why This Is The Smallest Useful Check

- It does not change the observer.
- It does not change the market universe.
- It does not add a new model family.
- It only asks whether the first PASS survives a more defensive, less hand-shaped allocation map.

# 6. What Would Count As A Useful Result

- If the branch still passes, the first result is less likely to be a one-off mapping artifact.
- If the branch fails immediately, the current branch is much weaker than the first PASS suggested.

# 7. Supervisor Instruction

- Run exactly one correction-style backtest with this mapping and compare it only against the first model run.
- Do not add more variants.
- Do not tune after seeing the result.
