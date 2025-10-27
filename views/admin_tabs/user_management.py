import streamlit as st

from services import persistence, admin as admin_svc
from services.survey import QUESTIONS
from ui.components import user_badge
from domain.constants import REGIONS, RANKS, INTERESTS


def render_user_management_tab():
    """Provides UI for managing users, including editing and deleting."""
    st.subheader("👤 사용자 관리")

    users = persistence.load_list('users')
    if not users:
        st.info("등록된 사용자가 없습니다.")
        return

    # Korean-first sorting: Hangul names (가-힣) come before any name starting with A-Za-z.
    import re

    def _kor_first_key(u):
        name = str(u.get('name', ''))
        # English name detection: starts with ASCII letter
        if re.match(r'^[A-Za-z]', name):
            return (1, name.lower())  # push to bottom
        return (0, name)  # Korean or other stays upper group
    users.sort(key=_kor_first_key)

    def _clean_name(n: str):
        return n[len('det_extra_'):] if isinstance(n, str) and n.startswith('det_extra_') else n
    display_map = {
        f"{_clean_name(u['name'])} ({u.get('employee_number','')}, {u['region']})": u['id'] for u in users}

    sel_disp = st.selectbox("사용자 선택", options=["-"] + list(display_map.keys()))
    if sel_disp == "-":
        st.markdown("---")
        st.subheader("사용자 목록")
        for u in users:
            # Temporarily augment name for badge display without mutating persistence.
            disp_user = {**u, 'name': _clean_name(u['name'])}
            user_badge(disp_user)
        return

    sel_id = display_map[sel_disp]
    user = next((u for u in users if u['id'] == sel_id), None)

    if user:
        with st.expander(f"편집: {_clean_name(user['name'])} ({user.get('employee_number','')}, {user['region']})", expanded=True):
            # The user editing form fields.
            new_name = st.text_input(
                "이름", value=user['name'], key=f"adm_edit_name_{sel_id}")
            new_emp = st.text_input("사번", value=user.get(
                'employee_number', ''), key=f"adm_edit_emp_{sel_id}")
            new_region = st.selectbox("지역", REGIONS, index=REGIONS.index(
                user['region']), key=f"adm_edit_region_{sel_id}")
            new_rank = st.selectbox("직급", RANKS, index=RANKS.index(
                user['rank']), key=f"adm_edit_rank_{sel_id}")
            new_interests = st.multiselect(
                "관심사", INTERESTS, default=user['interests'], key=f"adm_edit_interests_{sel_id}")

            st.markdown("**성향 설문**")
            existing_answers = user.get('survey_answers') or [
                3] * len(QUESTIONS)
            new_answers = [st.slider(
                q, 1, 5, existing_answers[i], key=f"adm_edit_q_{sel_id}_{i}") for i, q in enumerate(QUESTIONS)]

            # Action buttons
            col1, col2, col3 = st.columns(3)
            if col1.button("저장", key=f"adm_save_{sel_id}"):
                try:
                    updates = {
                        'name': new_name or "", 'employee_number': new_emp, 'region': new_region or "",
                        'rank': new_rank, 'interests': new_interests, 'survey_answers': new_answers
                    }
                    admin_svc.update_user_profile(sel_id, updates, users)
                    if sel_id == 'demo_user':
                        st.caption("(demo_user 변경 사항이 state 파일에 반영됨)")
                    st.success("업데이트 완료")
                    st.rerun()
                except ValueError as e:
                    st.error(e)

            if col2.button("삭제", key=f"adm_del_{sel_id}"):
                try:
                    admin_svc.delete_user(sel_id, users)
                    st.warning("삭제됨 (매칭 재실행 필요)")
                    st.rerun()
                except ValueError as e:
                    st.error(e)

            if col3.button("현재 사용자로 설정", key=f"adm_setcur_{sel_id}"):
                st.session_state.current_user_id = sel_id
                st.success("현재 사용자 세션이 업데이트되었습니다.")
