# 1. What This Branch Successfully Proved

- The event -> basket -> momentum -> MAD pipeline is implementable and runnable on the current Korea-equity daily data.
- The correction run proved that the worst first-run distortions could be removed without redesigning the branch.
- The branch can generate non-empty trades across multiple manually curated events under frozen rules.

# 2. What It Failed To Prove

- It did not prove stable risk-adjusted edge once the event sample was expanded beyond the trivial two-event case.
- It did not prove that the current event selection logic is robust enough to survive broader but still controlled event variation.
- It did not prove that this branch is strong enough to compete for core-strategy attention.

# 3. Why The Third Run Matters More Than The Correction Run

- The correction run mainly showed that the branch looked cleaner after structural fixes.
- The third run tested the same corrected structure on a less trivial event sample.
- That third run reduced the chance that the branch was only benefiting from an overly small and favorable initial sample.
- Once the sample widened, Sharpe and CAGR weakened materially.

# 4. Current Branch Status

- Structurally runnable, but strategically weak.
- The branch is no longer invalid because of obvious implementation distortion.
- It is now limited by mediocre results under the corrected structure.

# 5. Why This Is Not Ready As A Core Strategy

- The third run delivered only low positive CAGR and weak Sharpe.
- Drawdown remained meaningful even after the major structural corrections.
- The evidence base is still too small and too manually curated to justify promoting this branch into a core slot.
- The current results are not strong enough to justify more capital, complexity, or integration work.

# 6. What Would Justify Reopening This Branch Later

- A larger but still conservative event set that stays within the same frozen structure.
- Evidence that the branch can keep acceptable drawdown while improving Sharpe on a broader event sample.
- A clearer reason to believe the event mapping is causal rather than just descriptive.

# 7. Supervisor Verdict

- Keep this branch closed for now.
- It succeeded as a pipeline test, but not as a strategy candidate.
- Reopen only if a future test can broaden evidence without changing the frozen core structure.
