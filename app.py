import streamlit as st
import datetime as dt

# Import the page rendering functions from the new modules
from views import user_signup, my_club, activity_report, demo_script, admin_dashboard

# --- Page Registry ---
# Maps a page key to its label, rendering function from the imported module, and admin status.
PAGE_REGISTRY = {
    "user_signup": {
        "label": "프로필/설문",
        "render_func": user_signup.view,
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
    page_labels = [v["label"] for v in visible_pages.values()]

    # Page selection radio buttons
    # Use a session state variable to keep track of the current page
    if 'current_page' not in st.session_state:
        st.session_state.current_page = page_labels[0]

    selected_page_label = st.sidebar.radio(
        "메뉴 이동",
        page_labels,
        index=page_labels.index(
            st.session_state.current_page) if st.session_state.current_page in page_labels else 0,
        key="navigation_radio"
    )
    st.session_state.current_page = selected_page_label

    # Find the key corresponding to the selected label
    selected_page_key = page_keys[page_labels.index(selected_page_label)]

    # --- Page Rendering ---
    # Retrieve the render function from the registry and call it
    page_to_render = visible_pages[selected_page_key]["render_func"]
    page_to_render()

    # --- Footer ---
    st.sidebar.markdown("---")
    st.sidebar.caption(
        f"Data dir: data | {dt.datetime.now(dt.timezone.utc).strftime('%H:%M:%S')}Z"
    )


if __name__ == "__main__":
    main()
