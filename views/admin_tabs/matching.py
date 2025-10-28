import streamlit as st

from services import persistence, admin as admin_svc


def render_matching_tab():
    """Handles UI for running the matching algorithm."""
    st.subheader("⚙️ 매칭 실행")
    st.caption(
        "현재 활성/배정되지 않은(클럽 미소속) 사용자만 대상으로 신규 매칭을 수행합니다. 이미 클럽에 속한 사용자는 이번 실행에서 제외됩니다.")

    users_raw = persistence.load_list('users')
    if not users_raw:
        st.warning("매칭을 실행할 사용자가 없습니다. 먼저 사용자를 등록하거나 생성해주세요.")
        return

    effective_count = 0 if (len(users_raw) == 1 and users_raw[0].get(
        'id') == 'demo_user') else len(users_raw)
    st.info(f"현재 등록된 총 사용자: **{effective_count}명**")

    target_size = st.number_input(
        "클럽당 인원 (기본 6)", min_value=3, max_value=10, value=6, help="새 매칭 실행 시 한 클럽에 배정할 인원 수")
    # Execute button moved up into primary section (before separator)
    c_run, c_sep = st.columns([1, 5])
    with c_run:
        run_clicked = st.button("🚀 매칭 실행 / 새 버전 생성",
                                help="현재 사용자 목록으로 새로운 매칭 Run을 생성합니다.")
    st.write("---")
    # Removed redundant header '전체 재매칭' per request.

    if run_clicked:
        try:
            run_id, count = admin_svc.run_new_matching(target_size)
            st.success(f"새 매칭 실행 완료. Run ID: {run_id}, 생성된 클럽 수: {count}")
            st.balloons()
        except ValueError as e:
            st.error(e)
