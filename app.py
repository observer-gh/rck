import streamlit as st
import datetime as dt
from services import users as user_svc

# Import the page rendering functions from the new modules
from views import user_signup, my_club, activity_report, admin_dashboard, profile
from demo import demo_script

# --- Page Registry ---
# Maps a page key to its label, rendering function from the imported module, and admin status.
PAGE_REGISTRY = {
    "user_signup": {
        "label": "등록/설문",
        "render_func": user_signup.view,
        "admin": False,
    },
    "profile": {
        "label": "내 프로필",
        "render_func": profile.view,
        "admin": False,
    },
    "my_club": {
        "label": "내 클럽",
        "render_func": my_club.view,
        "admin": False,
    },
    "activity_report": {
        "label": "활동 보고",
        "render_func": activity_report.view,
        "admin": False,
    },
    "demo_script": {
        "label": "데모 가이드",
        "render_func": demo_script.view,
        "admin": False,
    },
    "admin_dashboard": {
        "label": "어드민 대시보드",
        "render_func": admin_dashboard.view,
        "admin": True,
    },
}


def main():
    """
    Main application router.

    This function controls the sidebar navigation and renders the selected page.
    It filters the available pages based on whether "Admin Mode" is active.
    """
    st.set_page_config(page_title="AI Club Matching Demo", layout="wide")

    # Ensure demo user exists and is the active session user.
    try:
        user_svc.load_users()  # guarantees demo user persistence
        st.session_state.current_user_id = 'demo_user'
    except Exception:
        # Fail silently if user bootstrap has an unexpected issue; app still usable.
        pass

    # --- Sidebar ---
    st.sidebar.title("Navigation")

    # Initialize session state for admin_mode if it doesn't exist
    if 'admin_mode' not in st.session_state:
        st.session_state.admin_mode = False

    # Admin mode toggle
    is_admin = st.sidebar.checkbox("Admin Mode", key="admin_mode")

    # Display a prominent banner at the top of the page if in admin mode
    if is_admin:
        st.info("관리자 모드가 활성화되었습니다. 모든 관리자 전용 메뉴를 볼 수 있습니다.", icon="👑")
        visible_pages = PAGE_REGISTRY
    else:
        visible_pages = {k: v for k,
                         v in PAGE_REGISTRY.items() if not v["admin"]}

    page_keys = list(visible_pages.keys())

    # Use a single source of truth: the radio widget's key is the nav state.
    if 'nav_page' not in st.session_state or st.session_state.nav_page not in page_keys:
        # Set a default before rendering the radio (only applies first render)
        st.session_state.nav_page = page_keys[0]

    st.sidebar.radio(
        "메뉴 이동",
        page_keys,
        key="nav_page",
        format_func=lambda k: visible_pages[k]["label"],
    )

    # --- Page Rendering ---
    # Retrieve the render function from the registry and call it
    # Use the up-to-date nav_page rather than the instantaneous selection variable
    page_to_render = visible_pages[st.session_state.nav_page]["render_func"]
    page_to_render()

    # --- Footer ---
    st.sidebar.markdown("---")
    st.sidebar.caption(
        f"Data dir: data | {dt.datetime.now(dt.timezone.utc).strftime('%H:%M:%S')}Z"
    )


if __name__ == "__main__":
    main()
