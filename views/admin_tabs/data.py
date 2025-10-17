import streamlit as st
import time

from services import admin as admin_svc

def render_data_tab():
    """Provides data management functions like export and reset."""
    st.subheader("💾 데이터 관리")

    with st.container(border=True):
        st.subheader("샘플 사용자 생성")
        if st.button("샘플 사용자 15명 생성"):
            admin_svc.add_sample_users(15)
            st.success("샘플 사용자 추가 완료!")
            st.rerun()

    with st.container(border=True):
        st.subheader("데이터 내보내기 (CSV)")
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("사용자"):
            st.download_button("다운로드: users.csv", admin_svc.export_to_csv('users'), "users.csv", "text/csv")
        if c2.button("클럽"):
            st.download_button("다운로드: clubs.csv", admin_svc.export_to_csv('clubs'), "clubs.csv", "text/csv")
        if c3.button("보고서"):
            st.download_button("다운로드: reports.csv", admin_svc.export_to_csv('activity_reports'), "reports.csv", "text/csv")
        if c4.button("매칭기록"):
            st.download_button("다운로드: runs.csv", admin_svc.export_to_csv('match_runs'), "runs.csv", "text/csv")

    with st.expander("🚨 Danger Zone: 데이터 초기화"):
        st.warning("주의: 이 작업은 모든 사용자, 클럽, 보고서, 매칭 기록을 영구적으로 삭제합니다. 되돌릴 수 없습니다.")
        if st.checkbox("위험을 인지했으며, 모든 데이터를 삭제하는 데 동의합니다."):
            if st.text_input("삭제를 원하시면 'ERASE ALL DATA'를 입력하세요.") == "ERASE ALL DATA":
                if st.button("모든 데이터 영구 삭제", type="primary"):
                    admin_svc.reset_all_data()
                    st.success("모든 애플리케이션 데이터가 삭제되었습니다 (데모사용자 제외).")
                    time.sleep(2)
                    st.rerun()