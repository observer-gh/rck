## Project Evolution Plan

This folder contains the structured phase plan for evolving the current Streamlit MVP into the next iteration that incorporates:

- Hard constraints & improved matching logic
- Personality (외향/내향/중간) survey & classification
- Report (activity) verification simulation with per-metric thresholds (AND logic)
- Data model extensions (employee number, unified ranks, club naming)
- Progressive polish & optional AI-like affordances (templated, not real model calls)

Approved decisions (confirmed by stakeholder):

1. Common Interest: Every member in a club must share at least one identical interest (global intersection size ≥ 1).
2. Personality Survey: 5 Likert (1–5) questions → aggregated to classify 외향 / 내향 / 중간.
3. Rank Diversity Objective: Only maximize the count of distinct ranks in each club (no distribution balancing).
4. Club Size: Minimum 5; existing upper bound (10) kept.
5. Report Verification: All three metrics must each pass individual thresholds (AND) to award points.
6. Club Name: Simple template first ("{지역} {대표관심사} {성향} 팀").
7. Personality Labels: 외향 / 내향 / 중간 (중간 replaces ‘밸런스’).
8. Migration: Map existing preferred_atmosphere values into personality_trait.
9. Points: Fixed 10 on pass, 0 on fail.

See individual phase documents for breakdown. A separate `jules-tasks.md` file sketches how each item can be represented as executable task units for a Jules-style workflow/orchestration system.
