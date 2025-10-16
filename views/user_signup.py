import streamlit as st
from typing import List, Dict, Any
from domain.models import User
from utils.ids import create_id_with_prefix
from services.survey import QUESTIONS, classify_personality
from services import users as user_svc

REGION_OPTIONS = ["서울", "부산", "대전", "대구"]
RANK_OPTIONS = ["사원", "대리", "과장", "차장", "부장"]
INTEREST_OPTIONS = ["축구", "영화보기", "보드게임", "러닝", "독서", "헬스", "요리", "사진", "등산"]


is_duplicate_user = user_svc.is_duplicate_user
load_users = user_svc.load_users
save_users = user_svc.save_users


def _profile_block(user: Dict[str, Any]):
    st.markdown(
        f"**이름:** {user['name']}  |  **지역:** {user['region']}  |  **직급:** {user['rank']}  |  **성향:** {user.get('personality_trait', '?')}")
    st.markdown(f"**관심사:** {', '.join(user['interests'])}")


def view():
    st.header("사용자 등록 및 프로필")
    admin_mode = st.session_state.get('admin_mode', False)

    # --- Creation Form (always available) ---
    with st.form("new_user_form"):
        st.subheader("신규 사용자 등록")
        name = st.text_input("이름", key="new_name")
        employee_number = st.text_input("사번", key="new_employee_number")
        region = st.selectbox("지역", REGION_OPTIONS, key="new_region")
        rank = st.selectbox("직급", RANK_OPTIONS, key="new_rank")
        interests = st.multiselect(
            "관심사", INTEREST_OPTIONS, key="new_interests")
        st.subheader("성향 설문")
        answers: list[int] = []
        for i, q in enumerate(QUESTIONS):
            # Preserve previously chosen value (defaults to 3 if none yet)
            default_val = st.session_state.get(f"q_{i}", 3)
            answer = st.slider(q, 1, 5, int(default_val), key=f"q_{i}")
            answers.append(answer)
        submitted = st.form_submit_button("저장")
        if submitted:
            if not (name and interests and employee_number):
                st.error("이름, 사번, 관심사를 모두 입력해야 합니다.")
            else:
                users = load_users()
                if is_duplicate_user(name, region, users):
                    st.error("중복 사용자 (이름+지역) 존재. 저장 취소.")
                else:
                    personality_trait = classify_personality(answers)
                    uid = create_id_with_prefix('u')
                    user = User(id=uid, name=name, employee_number=employee_number, region=region, rank=rank,
                                interests=interests, personality_trait=personality_trait, survey_answers=answers)
                    user_svc.append_user(user)
                    st.session_state.current_user_id = uid
                    st.success(f"저장 완료: {name} (성향: {personality_trait})")
                    # Clear form inputs explicitly after success (not on validation failure)
                    for k in ["new_name", "new_employee_number", "new_interests"]:
                        st.session_state[k] = "" if k != "new_interests" else [
                        ]
                    # Reset sliders to midpoint
                    for i in range(len(QUESTIONS)):
                        st.session_state[f"q_{i}"] = 3
                    # Region / rank keep last choice for convenience; comment out below if you want reset
                    # st.session_state["new_region"] = REGION_OPTIONS[0]
                    # st.session_state["new_rank"] = RANK_OPTIONS[0]
                    st.rerun()

    users = load_users()
    current_user_id = st.session_state.get('current_user_id')

    # --- User Mode (limited self view) ---
    if not admin_mode:
        st.divider()
        st.subheader("내 프로필")
        if current_user_id:
            me = next((u for u in users if u['id'] == current_user_id), None)
            if me:
                _profile_block(me)
                with st.expander("내 프로필 수정", expanded=False):
                    new_name = st.text_input(
                        "이름", value=me['name'], key=f"edit_name_{current_user_id}")
                    new_employee_number = st.text_input("사번", value=me.get(
                        'employee_number', ''), key=f"edit_emp_{current_user_id}")
                    new_region = st.selectbox("지역", REGION_OPTIONS, index=REGION_OPTIONS.index(
                        me['region']), key=f"edit_region_{current_user_id}")
                    new_rank = st.selectbox("직급", RANK_OPTIONS, index=RANK_OPTIONS.index(
                        me['rank']), key=f"edit_rank_{current_user_id}")
                    new_interests = st.multiselect(
                        "관심사", INTEREST_OPTIONS, default=me['interests'], key=f"edit_interests_{current_user_id}")
                    new_answers = []
                    existing_answers = me.get('survey_answers') or [
                        3]*len(QUESTIONS)
                    for i, q in enumerate(QUESTIONS):
                        new_answers.append(
                            st.slider(q, 1, 5, existing_answers[i], key=f"edit_q_{current_user_id}_{i}"))
                    if st.button("내 프로필 저장", key=f"save_self_{current_user_id}"):
                        safe_name = new_name or ""
                        safe_region = new_region or ""
                        if is_duplicate_user(safe_name, safe_region, users, exclude_id=current_user_id):
                            st.error("중복 사용자 (이름+지역) 존재. 변경 취소.")
                        else:
                            me.update({
                                'name': new_name,
                                'employee_number': new_employee_number,
                                'region': new_region,
                                'rank': new_rank,
                                'interests': new_interests,
                                'personality_trait': classify_personality(new_answers),
                                'survey_answers': new_answers
                            })
                            save_users(users)
                            st.success("업데이트 완료")
                            st.rerun()
            else:
                st.info("세션에 사용자 ID가 있으나 데이터를 찾을 수 없습니다. 새로 생성해주세요.")
        else:
            st.caption("아직 선택된/생성된 사용자가 없습니다. 위에서 새 사용자를 등록하면 여기에 표시됩니다.")
        return

    # --- Admin Mode (full list & CRUD) ---
    st.divider()
    st.subheader("현재 사용자 (편집/삭제)")
    if users:
        users.sort(key=lambda u: u['name'])
        display_map = {f"{u['name']} ({u['region']})": u['id'] for u in users}
        sel_disp = st.selectbox(
            "사용자 선택", options=["-"] + list(display_map.keys()))
        if sel_disp != "-":
            sel_id = display_map[sel_disp]
            st.session_state.current_user_id = sel_id
            u = next((x for x in users if x['id'] == sel_id), None)
            if u:
                with st.expander(f"편집: {u['name']} ({u['region']})", expanded=True):
                    new_name = st.text_input(
                        "이름", value=u['name'], key=f"edit_name_{sel_id}")
                    new_employee_number = st.text_input("사번", value=u.get(
                        'employee_number', ''), key=f"edit_emp_num_{sel_id}")
                    new_region = st.selectbox("지역", REGION_OPTIONS, index=REGION_OPTIONS.index(
                        u['region']), key=f"edit_region_{sel_id}")
                    new_rank = st.selectbox("직급", RANK_OPTIONS, index=RANK_OPTIONS.index(
                        u['rank']), key=f"edit_rank_{sel_id}")
                    new_interests = st.multiselect(
                        "관심사", INTEREST_OPTIONS, default=u['interests'], key=f"edit_interests_{sel_id}")
                    new_answers = []
                    existing_answers = u.get('survey_answers') or [
                        3] * len(QUESTIONS)
                    for i, q in enumerate(QUESTIONS):
                        answer = st.slider(
                            q, 1, 5, existing_answers[i], key=f"edit_q_{sel_id}_{i}")
                        new_answers.append(answer)
                    col1, col2 = st.columns(2)
                    if col1.button("저장 변경", key=f"save_user_{sel_id}"):
                        safe_name = new_name or ""
                        safe_region = new_region or ""
                        if is_duplicate_user(safe_name, safe_region, users, exclude_id=sel_id):
                            st.error("중복 사용자 (이름+지역) 존재. 변경 취소.")
                        else:
                            new_personality_trait = classify_personality(
                                new_answers)
                            u.update({
                                'name': new_name, 'employee_number': new_employee_number, 'region': new_region,
                                'rank': new_rank, 'interests': new_interests,
                                'personality_trait': new_personality_trait, 'survey_answers': new_answers
                            })
                            save_users(users)
                            st.success(
                                f"업데이트 완료 (성향: {new_personality_trait})")
                            st.rerun()
                    if col2.button("삭제", key=f"del_user_{sel_id}", type="primary"):
                        users = [x for x in users if x['id'] != sel_id]
                        save_users(users)
                        st.warning("삭제됨 (매칭 재실행 필요)")
                        st.rerun()
        st.subheader("사용자 목록")
        from ui.components import user_badge
        for user in users:
            user_badge(user)
    else:
        st.info("아직 등록된 사용자가 없습니다.")
