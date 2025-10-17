import streamlit as st

from services import admin as admin_svc

def render_analytics_tab():
    """Displays key metrics and analytics about the system."""
    st.subheader("📈 분석 및 현황")

    # Fetch analytics from the dedicated service function.
    analytics = admin_svc.get_system_analytics()

    # Display metrics in columns.
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 사용자", analytics["total_users"])
    c2.metric("총 클럽", analytics["total_clubs"])
    c3.metric("활성 클럽", analytics["active_clubs"])
    c4.metric("매칭 실행 횟수", analytics["total_match_runs"])
    c1.metric("보고서 (대기/검증)", f"{analytics['pending_reports']}/{analytics['verified_reports']}")
    c2.metric("총 포인트 (검증)", analytics["total_points_awarded"])
    c3.metric("평균 직급 다양성", f"{analytics['avg_rank_diversity']:.2f}")
    c4.metric("평균 관심사 다양성", f"{analytics['avg_interest_variety']:.2f}")

    st.write("---")
    st.subheader("클럽 포인트 순위 Top 5")

    top_clubs = admin_svc.get_top_clubs_by_points(limit=5)
    if top_clubs:
        # Prepare data for the bar chart.
        chart_data = {
            "클럽": [c['points'] for c in top_clubs],
            "이름": [c['name'] for c in top_clubs]
        }
        st.bar_chart(chart_data, x="이름", y="클럽")
    else:
        st.caption("검증된 포인트가 있는 클럽이 없습니다.")