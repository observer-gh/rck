import streamlit as st
import time

from services import activity

def render_verification_tab():
    """Allows admins to verify pending activity reports."""
    st.subheader("✅ 활동 보고서 검증")

    reports = activity.list_reports()
    pending = [r for r in reports if r['status'] == 'Pending']

    if not pending:
        st.info("검증 대기 중인 보고서가 없습니다.")
    else:
        st.write(f"**{len(pending)}**개의 보고서가 검증을 기다리고 있습니다.")
        for r in pending:
            with st.expander(f"Report `{r['id']}` | Club `{r['club_id']}` | Date: {r['date']}"):
                st.text_area("내용", r['formatted_report'], height=150, disabled=True)
                if st.button("AI 검증 실행", key=f"verify_{r['id']}"):
                    with st.spinner("AI 검증 시뮬레이션 중..."):
                        time.sleep(1) # Simulate delay
                        activity.verify_report(r['id'])
                    st.success("검증 완료! 포인트가 지급되었습니다.")
                    st.rerun()

    st.divider()
    st.subheader("검증 완료된 보고서")
    verified = [r for r in reports if r['status'] == 'Verified']
    st.dataframe(verified if verified else [], use_container_width=True)