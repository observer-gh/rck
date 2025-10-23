import streamlit as st
import datetime as dt
from ui.components.demo import render_demo_sidebar

# Import the page rendering functions from the new modules
from views import user_signup, my_club, activity_report, demo_script, admin_dashboard, profile

# --- Page Registry ---
# Maps a page key to its label, rendering function from the imported module, and admin status.
PAGE_REGISTRY = {
    "user_signup": {
        "label": "📝 프로필/설문",
        "render_func": user_signup.view,
        "admin": False,
    },
    "profile": {
        "label": "🙍 내 프로필",
        "render_func": profile.view,
        "admin": False,
    },
    "my_club": {
        "label": "👥 내 클럽",
        "render_func": my_club.view,
        "admin": False,
    },
    "activity_report": {
        "label": "🧾 활동 보고",
        "render_func": activity_report.view,
        "admin": False,
    },
    "demo_script": {
        "label": "🧪 데모 가이드",
        "render_func": demo_script.view,
        "admin": False,
    },
    "admin_dashboard": {
        "label": "🛠️ 어드민 대시보드",
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
    st.markdown("""<div style='padding:0.9rem 1.1rem; border-radius:10px; background:linear-gradient(135deg,#3f51b5,#5c6bc0); color:white; margin-bottom:1.0rem;'>
    <div style='font-size:1.05rem; font-weight:600;'>AI로 연결되는 사내 인적 네트워크</div>
    <div style='font-size:0.75rem; opacity:0.85;'>취향과 성향 기반 클럽 매칭 데모</div>
    </div>""", unsafe_allow_html=True)

    # Standard top demo panel
    render_demo_sidebar("global")

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

    # Handle deferred navigation target before creating radio (cannot set after instantiation)
    if 'nav_target' in st.session_state:
        target_label = st.session_state.nav_target
        # Validate target exists among labels
        if target_label in [v['label'] for v in PAGE_REGISTRY.values()]:
            # Preseed widget state key expected by radio
            st.session_state.navigation_radio = target_label
        del st.session_state.nav_target

    # Page selection radio buttons (single source of truth via widget state)
    selected_page_label = st.sidebar.radio(
        "메뉴 이동",
        page_labels,
        key="navigation_radio"
    )
    selected_page_key = page_keys[page_labels.index(selected_page_label)]

    # (Demo panel already rendered at top)

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
