# Split Models Promotion Defense Refresh

## Purpose

- freeze the current strongest after another batch of family exploration
- show why the strongest still stays even though several near-miss axes improved

## Current reading

- strongest:
  - `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
- broader challenger:
  - `hybrid_top2_plus_third00125`
- quality near-miss:
  - `bonus_recipient_top1_third_85_15`
- headline near-miss:
  - `tail_skip_entry_flowweakest_new_bottom4_top25_mid75`

## What changed in this search batch

- stronger / broader / quality / headline 축은 더 선명해졌습니다
- 하지만 strongest를 실제로 교체할 promotion-grade branch는 나오지 않았습니다
- 최근에 많이 본 새 family들은 대부분:
  - headline은 조금 좋아지지만 Sharpe robustness가 약했고
  - quality는 조금 좋아지지만 CAGR이 약했고
  - 어떤 건 아예 no-op 이었습니다

## Dead or Saturated Families

- quality-headline hybrid:
  - blended 숫자는 좋았지만 Sharpe 하락이 너무 큼
- risk-on exposure:
  - stronger branch를 못 만들고 오히려 약해짐
- risk-off tightening:
  - quality는 좋아져도 headline이 너무 약해짐
- entry filter:
  - 안정성은 좋아져도 strongest를 못 넘음
- hold buffer:
  - strongest와 사실상 동일한 no-op
- position-cap / sector-cap:
  - breadth는 좋아져도 알파 손실이 너무 큼
- flow filter / soft blacklist / dynamic bonus:
  - 구조 약점 완화보다 알파 훼손이 더 큼

## Verdict

- strongest는 그대로 유지하는 게 맞습니다
- recent search는 strongest replacement를 찾았다기보다, near-miss map을 더 정확하게 만든 검색 배치였습니다
- 다음 탐색은 dead family를 반복하지 말고, genuinely different family로 넘어가는 게 맞습니다
