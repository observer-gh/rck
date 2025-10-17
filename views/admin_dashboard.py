import streamlit as st

from views.admin_tabs.analytics import render_analytics_tab
from views.admin_tabs.user_management import render_user_management_tab
from views.admin_tabs.matching import render_matching_tab
from views.admin_tabs.clubs import render_clubs_tab
from views.admin_tabs.verification import render_verification_tab
from views.admin_tabs.data import render_data_tab

def view():
    """
    Renders the admin dashboard, which is organized into multiple tabs
    for different administrative functions.
    """
    st.header("어드민 대시보드")
    st.markdown("이곳에서 데이터 관리, 매칭 실행, 활동 보고서 검증 등 주요 관리 작업을 수행합니다.")

    tabs = st.tabs([
        "📈 분석 및 현황", "👤 사용자 관리", "⚙️ 매칭 실행",
        "📊 클럽 관리", "✅ 보고서 검증", "💾 데이터 관리"
    ])

    # Each tab is rendered by its own dedicated function for clarity.
    with tabs[0]:
        render_analytics_tab()
    with tabs[1]:
        render_user_management_tab()
    with tabs[2]:
        render_matching_tab()
    with tabs[3]:
        render_clubs_tab()
    with tabs[4]:
        render_verification_tab()
    with tabs[5]:
        render_data_tab()