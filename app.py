import streamlit as st
import datetime as dt
from urllib.parse import unquote
from ui.components.demo import render_demo_sidebar
from services import persistence
from domain.constants import DEMO_USER

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

    # Global survey radio pill styling (neutral smaller variant)
    st.markdown("""
    <style>
    div[data-testid="stRadio"] > label {font-weight:600; margin-bottom:0.2rem;}
    div[data-testid="stRadio"] div[role="radiogroup"] {display:flex; gap:.5rem; flex-wrap:wrap;}
    div[data-testid="stRadio"] label[data-baseweb="radio"] {border:1px solid #d2d5da; padding:.35rem .75rem; border-radius:999px; cursor:pointer; background:#f7f7f9; font-size:.8rem; color:#222; transition:background .15s,border-color .15s;}
    div[data-testid="stRadio"] label[data-baseweb="radio"]:hover {background:#eceff2; border-color:#b5b9bf;}
    div[data-testid="stRadio"] input:checked + div + label {background:#e2e4e7; border-color:#999; box-shadow:0 0 0 2px rgba(0,0,0,.06); color:#111; font-weight:600;}
    </style>
    """, unsafe_allow_html=True)

    # Ensure demo user exists & session locked
    users = persistence.load_list('users')
    if not any(u.get('id') == 'demo_user' for u in users):
        users.append(DEMO_USER.copy())
        persistence.replace_all('users', users)
    st.session_state.current_user_id = 'demo_user'

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
        st.info("관리자 모드: 대시보드가 열렸습니다.", icon="👑")
        # Remember last non-admin selection (once) to restore after exit
        if 'last_non_admin_page' not in st.session_state:
            # If a radio selection exists and it's non-admin, store it
            current_label = st.session_state.get('navigation_radio')
            if current_label:
                # Find key by label
                for _k, _v in PAGE_REGISTRY.items():
                    if _v['label'] == current_label and not _v.get('admin'):
                        st.session_state.last_non_admin_page = current_label
                        break
        # In admin mode we only show non-admin pages in radio (dashboard auto renders)
        visible_pages = {k: v for k,
                         v in PAGE_REGISTRY.items() if not v['admin']}
    else:
        # Leaving admin mode: restore previous non-admin page label if stored
        if 'last_non_admin_page' in st.session_state:
            st.session_state.navigation_radio = st.session_state.last_non_admin_page
            st.query_params['page'] = st.session_state.last_non_admin_page
            del st.session_state.last_non_admin_page
        visible_pages = {k: v for k,
                         v in PAGE_REGISTRY.items() if not v["admin"]}

    page_keys = list(visible_pages.keys())
    page_labels = [v["label"] for v in visible_pages.values()]

    # Query param persistence (new API)
    qs = st.query_params
    if 'nav_target' in st.session_state:
        target_label = st.session_state.nav_target
        if target_label in [v['label'] for v in PAGE_REGISTRY.values()]:
            st.session_state.navigation_radio = target_label
            # Use unified production API only
            st.query_params['page'] = target_label
        del st.session_state.nav_target
    elif 'page' in qs and 'navigation_radio' not in st.session_state:
        raw_param = qs.get('page')
        raw = unquote(raw_param) if isinstance(raw_param, str) else ''
        if raw in [v['label'] for v in PAGE_REGISTRY.values()]:
            st.session_state.navigation_radio = raw

    # Page selection radio buttons (single source of truth via widget state)
    selected_page_label = st.sidebar.radio(
        "메뉴 이동",
        page_labels,
        key="navigation_radio"
    )
    # Update query param when selection changes
    st.query_params['page'] = selected_page_label
    selected_page_key = page_keys[page_labels.index(selected_page_label)]

    # (Demo panel already rendered at top)

    # --- Page Rendering ---
    # Retrieve the render function from the registry and call it
    # Render admin dashboard automatically if admin mode is active
    if is_admin:
        admin_dashboard.view()
    else:
        page_to_render = visible_pages[selected_page_key]["render_func"]
        page_to_render()

    # --- Footer ---
    st.sidebar.markdown("---")
    st.sidebar.caption(
        f"Data dir: data | {dt.datetime.now(dt.timezone.utc).strftime('%H:%M:%S')}Z"
    )


if __name__ == "__main__":
    main()
