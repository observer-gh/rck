import streamlit as st

from services import persistence, admin as admin_svc
import importlib


def render_matching_tab():
    """Handles UI for running the matching algorithm."""
    st.subheader("⚙️ 매칭 실행")

    users_raw = persistence.load_list('users')
    if not users_raw:
        st.warning("매칭을 실행할 사용자가 없습니다. 먼저 사용자를 등록하거나 생성해주세요.")
        return

    st.info(f"현재 등록된 총 사용자: **{len(users_raw)}명**")

    # Demo explanation mode toggle (affects matching explanation detail level)
    matching_mod = importlib.import_module('services.matching')
    if 'demo_simple_explanations' not in st.session_state:
        st.session_state.demo_simple_explanations = matching_mod.DEMO_SIMPLE
    col_tog1, col_tog2 = st.columns([1, 3])
    with col_tog1:
        simple_mode = st.toggle("DEMO Simple Explanations", value=st.session_state.demo_simple_explanations,
                                help="ON: 간단한 데모 설명 문구 사용 / OFF: 상세 구조화된 지표")
    # Apply change if toggled
    if simple_mode != st.session_state.demo_simple_explanations:
        setattr(matching_mod, 'DEMO_SIMPLE', simple_mode)
        st.session_state.demo_simple_explanations = simple_mode
        st.toast(f"DEMO_SIMPLE = {simple_mode}")
    else:
        # Ensure module flag matches session
        if matching_mod.DEMO_SIMPLE != st.session_state.demo_simple_explanations:
            setattr(matching_mod, 'DEMO_SIMPLE',
                    st.session_state.demo_simple_explanations)

    # Special path for demo user to auto-generate more data.
    if len(users_raw) == 1 and users_raw[0].get('id') == 'demo_user':
        st.warning(
            "현재 데모 사용자 1명만 존재합니다. 아래 버튼으로 동료 9명을 자동 생성하고 즉시 매칭을 실행할 수 있습니다.")
        if st.button("동료 9명 자동생성 + 매칭 실행", type="primary"):
            try:
                run_id, count = admin_svc.generate_sample_users_and_match()
                st.success(
                    f"자동 생성 및 매칭 완료. Run ID: {run_id}, 생성된 클럽 수: {count}")
                st.balloons()
                st.rerun()
            except ValueError as e:
                st.error(e)

    target_size = st.number_input(
        "클럽당 인원 (기본 5)", min_value=3, max_value=10, value=5)
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
