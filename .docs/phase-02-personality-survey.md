## Phase 2 – Personality Survey & Classification

Goal: Replace manual/legacy atmosphere selection with a 5-question survey → classify into 외향/내향/중간.

Survey Draft (Likert 1–5: 1=Strongly Disagree, 5=Strongly Agree):

1. "새로운 사람들과 빠르게 친해지는 편이다."
2. "여러 사람 앞에서 말할 때 에너지가 생긴다."
3. "조용한 시간보다 다채로운 활동을 선호한다."
4. "즉흥적인 모임에 기꺼이 참여하는 편이다."
5. "대화에서 주도적으로 이야기한다."

Scoring (approved: A=OK):

- Sum = S (range 5..25).
- Thresholds (proposed):
  - S ≥ 18 → 외향
  - S ≤ 10 → 내향
  - Else → 중간
    (Adjustable constants; expose in config for tweaks.)

Implementation Steps:

1. Add a modal or stepper on User Signup after base fields; store raw answers as `personality_answers` (list[int]).
2. Derive classification on save; store to `personality_trait`.
3. Remove `preferred_atmosphere` from visible UI (keep for backward compatibility hidden until cleanup).
4. Add re-evaluate button in user edit to reclassify if answers edited (optional lower priority).

Testing:

- Edge cases: S=18, S=10 boundary values.
- Persist + reload retains trait & raw answers.

Exit Criteria:

- All new users classified only via survey (no direct select).
- Old users without answers keep migrated trait until they optionally complete survey.
