## Phase 4 – Activity Report Verification Simulation

Metrics (AND logic – all must pass):

1. Participants Similarity (P): Compare reported participant count vs. inferred (fake) photo count.
   - Simulation: If participant_override >=3 → P=0.85 else 0.65 (tunable).
   - Threshold: P ≥ 0.75.
2. Interest Relevance (I): Does raw_text contain primary_interest token (or any club interest)?
   - If contains primary_interest word → 0.9 else 0.5.
   - Threshold: I ≥ 0.70.
3. Photo Diversity (D): If multiple photos (future), for now simulate: single upload → 0.8, multiple distinct names → 0.85; if duplicates → 0.5.
   - Threshold: D ≥ 0.60.

Pass Condition: P ≥ 0.75 AND I ≥ 0.70 AND D ≥ 0.60.
Result:

- Pass → points_awarded = 10, status=Verified, verification_scores stored.
- Fail → points_awarded = 0, status=Verified, verification_scores stored, plus `verification_passed=false` flag.

UI:

- On verification action: show modal/alert summarizing each metric with green/red indicator.
- Table columns: participants_score, interest_score, diversity_score, passed.

Testing:

- Deterministic seeding of scores for reproducibility (use small helper function).
- Boundary tests: values exactly at threshold.

Config Surface:

- Place thresholds + point value in a dict (e.g. settings or constants module) for future tuning.

Exit Criteria:

- Verification path no longer blindly awards points.
- Scores visible and aligned with thresholds.
