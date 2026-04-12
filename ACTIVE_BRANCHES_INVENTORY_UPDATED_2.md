# 1. Closed Branches

- Event + Momentum + MAD
  - Status: Closed
  - Reason: Pipeline proved, strategy candidate failed to justify continued research.
  - Latest artifact: `D:\AI\모멘텀 투자\EVENT_MOMENTUM_MAD_BRANCH_VERDICT.md`

- US ETF Dual Momentum MVP v1
  - Status: Closed as a strategy branch
  - Reason: Backtest did not justify continued strategy work versus SPY.
  - Latest artifact: `D:\AI\모멘텀 투자\backtests\us_etf_dual_momentum_mvp_v1_batch2\decision_summary.csv`

# 2. Active Branches

- Global Flow Observer MVP
- Global Flow Observer First Model
- KR ETF Live Core

# 3. For Each Active Branch

## Global Flow Observer MVP
- Branch name: Global Flow Observer MVP
- Current purpose: Operator-facing observer for cross-asset capital rotation and regime reading.
- Current status: Built and usable.
- Latest meaningful artifact or output: `D:\AI\모멘텀 투자\GLOBAL_FLOW_OBSERVER_MONTHLY_MEMO_CURRENT.md`
- Whether it is closer to operator value or research value: Operator value

## Global Flow Observer First Model
- Branch name: Global Flow Observer First Model
- Current purpose: Test whether observer regimes can support a simple investable monthly allocation model.
- Current status: Open, but only as a secondary research candidate.
- Latest meaningful artifact or output: `D:\AI\모멘텀 투자\GLOBAL_FLOW_OBSERVER_FIRST_MODEL_FINAL_BRANCH_VERDICT.md`
- Whether it is closer to operator value or research value: Research value

## KR ETF Live Core
- Branch name: KR ETF Live Core
- Current purpose: Maintain the existing Korea ETF live operating decision path.
- Current status: Operational, but not current research focus.
- Latest meaningful artifact or output: `D:\AI\모멘텀 투자\live_core\kr_etf_riskbudget\backtests\kis_go_stop_report.csv`
- Whether it is closer to operator value or research value: Operator value

# 4. Which Single Branch Should Be Prioritized Now

- Global Flow Observer MVP

# 5. Why That Branch Is The Best Use Of Time

- It is already built and directly supports operator judgment.
- The first model derived from it is only secondary, not core.
- Improving decision usefulness of the observer is still a higher-value use of time than pushing a weak return branch further.

# 6. What Must Not Be Touched Now

- Do not reopen the Event + Momentum + MAD branch.
- Do not reopen the US ETF Dual Momentum strategy branch.
- Do not promote the Global Flow Observer First Model into a core strategy branch.
- Do not touch KR ETF Live Core.
