import streamlit as st

from services import persistence, admin as admin_svc


def render_matching_tab():
    """Handles UI for running the matching algorithm."""
    st.subheader("⚙️ 매칭 실행")

    users_raw = persistence.load_list('users')
    if not users_raw:
        st.warning("매칭을 실행할 사용자가 없습니다. 먼저 사용자를 등록하거나 생성해주세요.")
        return

    effective_count = 0 if (len(users_raw) == 1 and users_raw[0].get(
        'id') == 'demo_user') else len(users_raw)
    st.info(f"현재 등록된 총 사용자: **{effective_count}명**")

    target_size = st.number_input(
        "클럽당 인원 (기본 6)", min_value=3, max_value=10, value=6)
    st.write("---")
    st.subheader("전체 재매칭")
    st.warning("주의: 이 작업은 기존 클럽에 영향을 주지 않고 새로운 클럽들을 추가 생성합니다.")

    if st.button("매칭 실행 / 새 버전 생성"):
        try:
            run_id, count = admin_svc.run_new_matching(target_size)
            st.success(f"새 매칭 실행 완료. Run ID: {run_id}, 생성된 클럽 수: {count}")
            st.balloons()
        except ValueError as e:
            st.error(e)
