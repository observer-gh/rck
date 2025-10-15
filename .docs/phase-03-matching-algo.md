## Phase 3 – New Matching Algorithm (Hard Constraints + Diversity)

Objectives:

1. Hard constraints: All members share (a) same region, (b) same personality_trait, (c) at least one common interest (global intersection ≥1).
2. Optimize: maximize count of distinct ranks per club.
3. Derive `primary_interest` (rule: choose the common interest with highest global frequency among matched members; tie-break lexicographically).
4. Generate club `name` via template: "{region} {primary_interest} {personality_trait} 팀".
5. Add `summary` string: e.g., "서울 · 축구 · 외향 · 직급 4종".

Algorithm Sketch (Greedy Heuristic):

1. Group users by (region, personality_trait).
2. Within each bucket, build inverse index interest→[users].
3. Candidate seeds = interests with ≥5 users.
4. For each seed interest, build a pool of users containing that interest. Select subsets that maximize distinct rank count:
   - Score(candidate_set) = (#distinct_ranks, -|candidate_set| variance to target_size).
5. Use greedy selection: repeatedly pick highest-scoring subset (size ≥5) removing those users from availability.
6. Remainder handling: attempt to merge leftover users via second-pass relaxation (skip if leftover <5).

Data Additions (Club):

- name: str
- primary_interest: str
- personality_trait: str (redundant but convenient)
- summary: str

Explanations Update:

- Present reasons summary line: "공통 관심사 축구 | 지역 서울 | 성향 외향 | 직급 다양성 4종 (사원/대리/과장/부장)".

Testing:

- Ensure each club passes constraints.
- Ensure distinct ranks count is non-decreasing relative to random baseline in test fixtures.
- Test `primary_interest` selection rule.

Exit Criteria:

- All generated clubs satisfy constraints.
- Name + summary rendered in UI list view.
