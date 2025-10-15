## Phase 6 – Multi-Page Demo View Split (User vs Admin)

Goal: Provide a clear demo narrative separating end-user journey from admin operations without implementing production-grade auth.

Decisions (Confirmed):

1. Page mechanism: 1b → Single-file router with sidebar selectbox (dynamic hiding easier than native pages folder).
2. Admin toggle style: 2b → Single checkbox (keep friction minimal for demo flow).
3. Passphrase: 3b → None (demo speed prioritized; not security focused).
4. Demo Script visibility: 4c → User-visible (lets audience follow along; keep non-destructive).
5. Reports page structure: 5a → Combined submit + status page.
6. Matching runs grouping: 6b → Combined inside “Admin Dashboard” using internal tabs.
7. User navigation order: 7a → Profile first (logical start of journey).
8. Club visibility for users: 8a → Only their club (privacy narrative, reduce noise).
9. Analytics inclusion now: 9a → Minimal counts (runs, users, verified reports) in Admin Dashboard.

User Pages:

- Profile / Signup (create or edit current user; personality mapping interim)
- My Club (assigned club or placeholder “Awaiting matching by admin”)
- Activity Report (submit + status inline)
- How It Works (simple explanation + diagram placeholder)
- Demo Script (walkthrough steps; read-only)

Admin Dashboard (visible only when Admin Mode ON checkbox checked):
Tabs:

- Matching (run match, run history, basic metrics)
- Clubs (club compositions, diversity indicators)
- Reports (pending list, verify action, archive toggle)
- Data & Tools (seed users, import/export, thresholds view, danger zone with double confirm)
- Analytics (minimal metrics counts; future expansion)

Visual Indicators:

- Top banner when admin mode active: “ADMIN MODE (Demo Only)” with subtle amber background.
- Danger Zone behind additional confirmation checkbox.

State Additions:

- session_state.admin_mode (bool)
- session_state.current_user_id (persist chosen user)

Refactors:

- Extract UI component helpers into `ui/components.py` (e.g., user_badge, club_card, metric_chip).
- Move matching trigger & destructive ops exclusively under Admin tab guard.

Testing Additions:

- Smoke import test for router building page list according to admin_mode.
- Test ensuring user view cannot call run_matching function (guard raises / hidden).
- Test placeholder text appears when user has no club.

Exit Criteria:

- Single Streamlit app shows only user pages with admin mode unchecked.
- Admin Dashboard & banner appear when checkbox enabled.
- No user path exposes matching or danger zone.
- Tests pass.

Risks & Mitigations:

- Accidental exposure of admin controls → dynamic filtering of page registry before render.
- Confusion over Demo Script page being user-visible → keep content instructional, non-interactive.
- UI clutter in Admin Dashboard → use tabs to compress breadth.

Future Auth Path (Not in Scope):

- Replace checkbox with role claim after SSO integration.
- Persist roles in user model and restrict operations server-side.
