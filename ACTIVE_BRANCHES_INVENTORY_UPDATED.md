# 1. Closed Branches

- **Event + Momentum + MAD**
  - Status: Closed
  - Reason: The branch proved the pipeline could run, but the corrected third run was too weak to justify further time now.
  - Latest artifact: `D:\AI\모멘텀 투자\EVENT_MOMENTUM_MAD_BRANCH_VERDICT.md`

- **US ETF Dual Momentum MVP v1**
  - Status: Closed as a strategy branch
  - Reason: The backtest did not beat simple SPY buy-and-hold on return or Sharpe, so it is not worth pursuing as the next model branch.
  - Latest artifact: `D:\AI\모멘텀 투자\backtests\us_etf_dual_momentum_mvp_v1_batch2\decision_summary.csv`

# 2. Active Branches

- **Global Flow Observer MVP**
- **KR ETF Live Core**

# 3. For Each Active Branch

## Global Flow Observer MVP
- Branch name: Global Flow Observer MVP
- Current purpose: Show current cross-asset capital rotation and recent regime change in a compact operator-facing dashboard.
- Current status: Built and usable as an observer layer.
- Latest meaningful artifact or output: `D:\AI\모멘텀 투자\GLOBAL_FLOW_OBSERVER_MONTHLY_MEMO_CURRENT.md`
- Closer to operator value or research value: Operator value

## KR ETF Live Core
- Branch name: KR ETF Live Core
- Current purpose: Maintain the existing Korea ETF operating path for monthly or periodic live decision support.
- Current status: Operational branch exists, but not the main exploration direction.
- Latest meaningful artifact or output: `D:\AI\모멘텀 투자\live_core\kr_etf_riskbudget\backtests\kis_go_stop_report.csv`
- Closer to operator value or research value: Operator value

# 4. Which Single Branch Should Be Prioritized Now

- **Global Flow Observer MVP**

# 5. Why That Branch Is The Best Use Of Time

- It is the only active branch in this thread that directly addresses the unresolved core problem: understanding capital rotation before building another strategy.
- It already has a working data pipeline, outputs, dashboard, and monthly memo path.
- It is closer to immediate decision support than a new research branch would be.
- It avoids repeating the pattern of building another model before the observation layer is strong enough.

# 6. What Must Not Be Touched Now

- Do not reopen the Event + Momentum + MAD branch.
- Do not restart the US ETF Dual Momentum model branch.
- Do not widen the Global Flow Observer scope into a platform, dashboard redesign project, or new strategy engine.
- Do not spend time on parameter tuning or new model branches before the observer layer proves its operator value.
