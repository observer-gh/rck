import streamlit as st
from services import persistence
from domain.models import User
from utils.ids import create_id_with_prefix
from services.survey import QUESTIONS, classify_personality
from dataclasses import asdict
from typing import Optional, List, Dict, Any

# --- Constants ---
REGION_OPTIONS = ["서울", "부산", "대전", "대구"]
RANK_OPTIONS = ["사원", "대리", "과장", "차장", "부장"]
INTEREST_OPTIONS = ["축구", "영화보기", "보드게임", "러닝", "독서", "헬스", "요리", "사진", "등산"]

# --- Utility Functions (to be refactored into a shared module) ---

def is_duplicate_user(name: str, region: str, users: List[Dict[str, Any]], exclude_id: Optional[str] = None) -> bool:
    """Check if a (name, region) combo already exists (case-insensitive)."""
    name_norm = name.strip().lower()
    region_norm = region.strip().lower()
    for u in users:
        if exclude_id and u['id'] == exclude_id:
            continue
        if u['name'].strip().lower() == name_norm and u['region'].strip().lower() == region_norm:
            return True
    return False

def load_users():
    return persistence.load_list('users')

def save_users(users):
    persistence.replace_all('users', users)

# --- Page Rendering Function ---

def view():
    """Renders the user signup, edit, and profile survey page."""
    st.header("사용자 등록 및 프로필")

    with st.form("new_user_form", clear_on_submit=True):
        st.subheader("신규 사용자 등록")
        name = st.text_input("이름")
        employee_number = st.text_input("사번")
        region = st.selectbox("지역", REGION_OPTIONS)
        rank = st.selectbox("직급", RANK_OPTIONS)
        interests = st.multiselect("관심사", INTEREST_OPTIONS)

        st.subheader("성향 설문")
        answers = []
        for i, q in enumerate(QUESTIONS):
            answer = st.slider(q, 1, 5, 3, key=f"q_{i}")
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
                    users.append(asdict(user))
                    save_users(users)
                    st.success(f"저장 완료: {name} (성향: {personality_trait})")

    st.divider()
    st.subheader("현재 사용자 (편집/삭제)")
    users = load_users()
    if users:
        users.sort(key=lambda u: u['name'])
        display_map = {f"{u['name']} ({u['region']})": u['id'] for u in users}
        sel_disp = st.selectbox("사용자 선택", options=["-"] + list(display_map.keys()))

        if sel_disp != "-":
            sel_id = display_map[sel_disp]
            u = next((x for x in users if x['id'] == sel_id), None)
            if u:
                with st.expander(f"편집: {u['name']} ({u['region']})", expanded=True):
                    new_name = st.text_input("이름", value=u['name'], key=f"edit_name_{sel_id}")
                    new_employee_number = st.text_input("사번", value=u.get('employee_number', ''), key=f"edit_emp_num_{sel_id}")
                    new_region = st.selectbox("지역", REGION_OPTIONS, index=REGION_OPTIONS.index(u['region']), key=f"edit_region_{sel_id}")
                    new_rank = st.selectbox("직급", RANK_OPTIONS, index=RANK_OPTIONS.index(u['rank']), key=f"edit_rank_{sel_id}")
                    new_interests = st.multiselect("관심사", INTEREST_OPTIONS, default=u['interests'], key=f"edit_interests_{sel_id}")

                    st.subheader("성향 설문 (재실시)")
                    new_answers = []
                    existing_answers = u.get('survey_answers') or [3] * len(QUESTIONS)
                    for i, q in enumerate(QUESTIONS):
                        answer = st.slider(q, 1, 5, existing_answers[i], key=f"edit_q_{sel_id}_{i}")
                        new_answers.append(answer)

                    col1, col2 = st.columns(2)
                    if col1.button("저장 변경", key=f"save_user_{sel_id}"):
                        if is_duplicate_user(new_name, new_region, users, exclude_id=sel_id):
                            st.error("중복 사용자 (이름+지역) 존재. 변경 취소.")
                        else:
                            new_personality_trait = classify_personality(new_answers)
                            u.update({
                                'name': new_name, 'employee_number': new_employee_number, 'region': new_region,
                                'rank': new_rank, 'interests': new_interests,
                                'personality_trait': new_personality_trait, 'survey_answers': new_answers
                            })
                            save_users(users)
                            st.success(f"업데이트 완료 (성향: {new_personality_trait})")
                            st.rerun()

                    if col2.button("삭제", key=f"del_user_{sel_id}", type="primary"):
                        users = [x for x in users if x['id'] != sel_id]
                        save_users(users)
                        st.warning("삭제됨 (매칭 재실행 필요)")
                        st.rerun()


        st.subheader("사용자 목록")
        for user in users:
            from ui.components import user_badge
            user_badge(user)

    else:
        st.info("아직 등록된 사용자가 없습니다.")