# Split Models Dead Family Ledger

## Purpose

- current strongest 아래에서 dead or no-op 로 확인된 family를 고정합니다
- 같은 축을 반복해서 다시 여는 탐색 낭비를 줄이기 위한 문서입니다

## Current strongest

- `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`

## Current dead / no-op reading

- dead:
  - quality-headline hybrid
  - risk-on exposure
  - risk-off tightening
  - entry filter
  - position cap
  - sector cap relaxation
  - flow filter
  - soft blacklist
  - dynamic bonus sizing
  - liquidity gate
- no-op:
  - hold buffer
  - KR unknown exclusion

## Why this matters

- 최근 batch는 near-miss map을 넓히는 데는 성공했습니다
- 하지만 동시에 “더 이상 mainline strongest search에 쓸 가치가 낮은 축”도 꽤 많이 확정했습니다
- 이 ledger는 다음 탐색이 genuinely different family로 넘어가도록 하는 guardrail 역할을 합니다

## Verdict

- 위 family들은 현 strongest 기준으로 반복 탐색 우선순위에서 내리는 게 맞습니다
- 다음 탐색은 dead/no-op 축이 아니라, 아직 안 본 구조 family로 가는 게 맞습니다
