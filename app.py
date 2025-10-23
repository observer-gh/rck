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
    },
    "profile": {
        "label": "🙍 내 프로필",
        "render_func": profile.view,
    },
    "my_club": {
        "label": "👥 내 클럽",
        "render_func": my_club.view,
    },
    "activity_report": {
        "label": "🧾 활동 보고",
        "render_func": activity_report.view,
    },
    "demo_script": {
        "label": "🧪 데모 가이드",
        "render_func": demo_script.view,
    },
    "admin_dashboard": {
        "label": "🛠️ 어드민 대시보드",
        "render_func": admin_dashboard.view,
    },
}


def main():
    """
    Main application router.

    This function controls the sidebar navigation and renders the selected page.
    It filters the available pages based on whether the Admin Dashboard mode is active.
    """
    st.set_page_config(page_title="AI Club Matching Demo", layout="wide")

    # (Removed admin_mode toggle; admin dashboard now a direct page selection)

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

    # Admin dashboard accessed via a button; radio always visible for normal pages
    non_admin_pages = {k: v for k,
                       v in PAGE_REGISTRY.items() if k != 'admin_dashboard'}
    admin_label = PAGE_REGISTRY['admin_dashboard']['label']
    if 'active_page' not in st.session_state:
        # default to first non-admin page key
        st.session_state.active_page = next(iter(non_admin_pages.keys()))
    # Admin button
    if st.sidebar.button(admin_label):
        st.session_state.active_page = 'admin_dashboard'
        st.session_state._admin_clicked = True
        st.query_params['page'] = admin_label
    visible_pages = non_admin_pages

    page_keys = list(visible_pages.keys())
    page_labels = [v["label"] for v in visible_pages.values()]

    # Query param persistence (new API)
    qs = st.query_params
    if 'nav_target' in st.session_state:
        target_label = st.session_state.nav_target
        all_labels = [v['label'] for v in PAGE_REGISTRY.values()]
        if target_label in all_labels:
            if target_label == admin_label:
                st.session_state.active_page = 'admin_dashboard'
            else:
                st.session_state.navigation_radio = target_label
                st.session_state.active_page = next(
                    k for k, v in non_admin_pages.items() if v['label'] == target_label)
            st.query_params['page'] = target_label
        del st.session_state.nav_target
    elif 'page' in qs and 'navigation_radio' not in st.session_state and 'active_page' in st.session_state:
        raw_param = qs.get('page')
        raw = unquote(raw_param) if isinstance(raw_param, str) else ''
        all_labels = [v['label'] for v in PAGE_REGISTRY.values()]
        if raw in all_labels:
            if raw == admin_label:
                st.session_state.active_page = 'admin_dashboard'
            else:
                st.session_state.navigation_radio = raw
                st.session_state.active_page = next(
                    k for k, v in non_admin_pages.items() if v['label'] == raw)

    # Always show radio for non-admin pages
    selected_page_label = st.sidebar.radio(
        "메뉴 이동",
        page_labels,
        key="navigation_radio"
    )
    # Only override active_page if not currently viewing admin dashboard
    if st.session_state.active_page != 'admin_dashboard' and selected_page_label:
        st.session_state.active_page = next(
            k for k, v in non_admin_pages.items() if v['label'] == selected_page_label)
        st.query_params['page'] = selected_page_label

    # (Demo panel already rendered at top)

    # --- Page Rendering ---
    # Resolve render function based on active_page
    active_key = st.session_state.active_page
    if active_key == 'admin_dashboard':
        PAGE_REGISTRY['admin_dashboard']["render_func"]()
        st.caption("관리자 전용 페이지 · 아래 메뉴로 일반 페이지 이동")
        # Provide an exit button back to the selected radio page
        exit_col = st.columns(1)[0]
        with exit_col:
            if st.button("← 일반 페이지 보기", key="exit_admin"):
                # revert to current radio selection
                radio_label = st.session_state.get(
                    'navigation_radio') or page_labels[0]
                st.session_state.active_page = next(
                    k for k, v in non_admin_pages.items() if v['label'] == radio_label)
                st.query_params['page'] = radio_label
                st.rerun()
    else:
        page_to_render = PAGE_REGISTRY[active_key]["render_func"]
        page_to_render()

    # --- Footer ---
    st.sidebar.markdown("---")
    st.sidebar.caption(
        f"Data dir: data | {dt.datetime.now(dt.timezone.utc).strftime('%H:%M:%S')}Z"
    )


if __name__ == "__main__":
    main()
