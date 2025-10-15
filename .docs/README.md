## Demo View Split Plan (Narrow Scope)

This `.docs` folder now contains ONLY the focused plan to introduce a multi-page separation between end-user and admin flows inside the existing Streamlit app for demo purposes. All previous multi-phase roadmap documents were intentionally removed to reduce cognitive load and keep the narrative tight.

### Objective

Deliver a clean demo where:

1. A user can sign up, view (or await) their club, submit an activity report, and read a demo script guidance page.
2. An admin (via a simple checkbox toggle) can access a dashboard with matching, clubs overview, reports verification, data tools, and minimal analytics.
3. No production authentication is implemented; separation is purely a presentation + safety device.

### Key Elements

- Dynamic page registry with sidebar selection.
- `admin_mode` checkbox controlling which pages appear.
- Tabbed Admin Dashboard (matching | clubs | reports | data | analytics).
- Shared UI components module for reusable cards/badges.
- Double-confirm Danger Zone protections.
- Placeholder message when a user has no club assigned yet.
- User-visible Demo Script page to guide observers through the flow.

### Source of Truth

`jules-plan.yaml` defines a single Phase (Phase 1) containing atomic tasks (audit, router scaffold, extraction, toggle, banner, dashboard tabs, placeholder, components, guard, analytics, demo script, smoke tests, README refresh).

### Out of Scope (Explicitly Deferred)

- Personality survey mechanics
- Advanced matching rework / hard constraints re-introduction
- Verification metric simulation logic changes
- Extended data exports/imports
- Partial rematch feature
- Real authentication & role persistence

### Next Step

Implement tasks in order. Begin with `p1.audit_current_app` to capture the existing UI segments before refactor.

---

This narrowed plan can be expanded later by reintroducing phased documents if strategic scope returns. For now, lean focus maximizes demo readiness speed.
