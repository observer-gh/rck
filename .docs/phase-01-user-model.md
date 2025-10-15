## Phase 1 – User Model & Basic Constraints Prep

Goal: Adjust the data foundation to support new constraints without breaking current flows.

Scope:

1. Rank list normalization → ["사원", "대리", "과장", "차장", "부장"] (remove "주임").
2. Add `employee_number` field to `User` (string, required in UI; uniqueness guard optional – TBD).
3. Introduce `personality_trait` field (enum: 외향 | 내향 | 중간). Temporarily populate from legacy `preferred_atmosphere` until survey lands.
4. Enforce minimum group size = 5 at matching initiation (UI validation + backend guard).
5. Prepare helper to compute global interest intersection to validate groups (placeholder in matching service for Phase 3 actual use).

Migration Plan:

- When loading users, if `personality_trait` absent and `preferred_atmosphere` present, map:
  - 외향→외향, 내향→내향, 밸런스→중간, 기타→중간.
- Optionally write back migrated field on save.

Testing (add):

- Test migration mapping.
- Test rank list no longer contains 주임.
- Test that creating a club below size 5 is prevented (simulate matching with <5 users → no run or explicit error).

Risks / Mitigations:

- Existing JSONs missing new fields → handled by default values.
- UI confusion during interim (survey not yet implemented) → add small tooltip “(임시 자동 분류)” next to personality display.

Exit Criteria:

- All users have personality_trait.
- UI shows new rank list & employee number input.
- Tests green.
