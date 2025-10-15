## Jules Task Mapping (Draft)

If using a "Jules" style orchestrator (task runner / automation agent), below are suggested atomic tasks. Each task lists: id, phase, description, inputs, outputs, done criteria.

```yaml
tasks:
  - id: phase1.migrate_ranks
    phase: 1
    desc: Normalize rank list & remove legacy value.
    outputs: [updated_user_json]
    done: rank set matches spec; tests green.

  - id: phase1.add_employee_number
    phase: 1
    desc: Add employee_number field + UI input + duplicate optional check.
    done: new users require employee_number.

  - id: phase1.personality_migration
    phase: 1
    desc: Map preferred_atmosphere→personality_trait; write back.
    done: all user records have personality_trait.

  - id: phase2.survey_ui
    phase: 2
    desc: Implement 5-question Likert survey for new signup.
    done: manual trait selection removed.

  - id: phase2.classify_trait
    phase: 2
    desc: Apply scoring thresholds to answers.
    done: boundary test cases pass.

  - id: phase3.match_core
    phase: 3
    desc: Implement hard constraints filter & greedy grouping.
    done: all clubs satisfy region/personality/common-interest.

  - id: phase3.primary_interest
    phase: 3
    desc: Compute club primary_interest & summary.
    done: field present on all clubs.

  - id: phase3.club_naming
    phase: 3
    desc: Generate template-based club name.
    done: name displayed in UI list view.

  - id: phase4.verification_metrics
    phase: 4
    desc: Implement scoring simulation (P/I/D) + thresholds.
    done: failing reports yield 0 pts, passing yield 10.

  - id: phase4.verification_ui
    phase: 4
    desc: Modal/alert summarizing metric results.
    done: user sees pass/fail rationale.

  - id: phase5.partial_rematch
    phase: 5
    desc: Allow selecting users and regenerating only their club.
    done: unaffected clubs stable; tests updated.

  - id: phase5.cleanup_legacy
    phase: 5
    desc: Remove preferred_atmosphere usage.
    done: no references remain; migration script archived.
```

You can feed these task identifiers into Jules (or adapt format) to drive execution, tracking status (pending/in-progress/done) and attaching logs.

Next: Confirm if you want a single aggregated YAML (e.g., `.docs/jules-plan.yaml`) for machine consumption.
