# App.py UI Audit (Pre-Refactor)

This document inventories the UI components in the monolithic `app.py` before the "view split" refactoring. The goal is to categorize each piece of the UI as either user-facing, admin-facing, or mixed-use.

## I. Sidebar Components

The sidebar contains navigation and several utility panels.

| Component         | Type    | Description                                                                 | Target Page/Component          |
| ----------------- | ------- | --------------------------------------------------------------------------- | ------------------------------ |
| **Navigation**    | Mixed   | A `st.sidebar.radio` selector that controls which "page" is displayed.      | `app.py` (Router)              |
| **Health/Metrics**| Admin   | Expander with app-wide stats (users, clubs, reports).                       | `pages/admin_dashboard.py`     |
| **Analytics**     | Admin   | Expander with club diversity metrics.                                       | `pages/admin_dashboard.py`     |
| **Demo Guide**    | Admin   | Expander with buttons to seed users and run a quick match.                  | `app.py` (Sidebar logic)       |
| **Danger Zone**   | Admin   | Expander with a button to erase all application data.                       | `pages/admin_dashboard.py`     |
| **Show IDs**      | Mixed   | A checkbox to toggle the visibility of internal database IDs.               | `app.py` (Global state)        |

## II. Main Page Views

The main content area is controlled by the sidebar radio button selection.

| Page Name               | Type    | Description                                                                                                   | Target Page/Component        |
| ----------------------- | ------- | ------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| **User Signup**         | User    | Form for creating a new user profile and editing/deleting existing ones. Includes a personality survey.       | `pages/user_signup.py`       |
| **Matching (Admin)**    | Admin   | UI for triggering full or partial matchmaking runs.                                                           | `pages/admin_dashboard.py` (Tab: Matching) |
| **Results**             | Mixed   | Displays all clubs from a selected match run. Admin-focused view. A user-centric view needs to be derived.    | `pages/my_club.py` (User) & `pages/admin_dashboard.py` (Tab: Clubs) |
| **Activity Reports**    | User    | Form for a user to submit an activity report for their active club.                                           | `pages/activity_report.py`   |
| **Verification (Admin)**| Admin   | Interface for admins to review and verify pending activity reports, simulating an AI check.                     | `pages/admin_dashboard.py` (Tab: Verification) |
| **Match Runs**          | Admin   | A table view showing the history of all matchmaking runs.                                                     | `pages/admin_dashboard.py` (Tab: Data) |
| **Seed Sample Users**   | Admin   | UI for generating sample users and importing/exporting user data via CSV.                                     | `pages/admin_dashboard.py` (Tab: Data) |

## III. Refactoring Plan Summary

-   **User Flow:**
    1.  `pages/user_signup.py`: Create/edit profile.
    2.  `pages/my_club.py`: View assigned club details (or a placeholder if not assigned).
    3.  `pages/activity_report.py`: Submit reports for the club.
    4.  `pages/demo_script.py`: A static page with guidance for the demo.

-   **Admin Flow (consolidated into `pages/admin_dashboard.py` with tabs):**
    1.  **Matching Tab:** Run and re-run matches.
    2.  **Clubs Tab:** Overview of all clubs.
    3.  **Verification Tab:** Verify activity reports.
    4.  **Data Tab:** Manage sample data, view match run history.
    5.  **Analytics Tab:** Display high-level metrics.
    6.  **Danger Zone:** Will be a section on one of the admin tabs.

-   **Core App Logic (`app.py`):**
    -   Will be refactored into a router.
    -   Will hold the "Admin Mode" toggle in the sidebar.
    -   Will manage the page registry and display the selected page.