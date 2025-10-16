import streamlit as st
from typing import List, Dict, Any
from domain.models import User
from utils.ids import create_id_with_prefix
from services.survey import QUESTIONS, classify_personality
from services import users as user_svc
from ui.components import render_demo_actions_panel

REGION_OPTIONS = ["서울", "부산", "대전", "대구"]
RANK_OPTIONS = ["사원", "대리", "과장", "차장", "부장"]
INTEREST_OPTIONS = ["축구", "영화보기", "보드게임", "러닝", "독서", "헬스", "요리", "사진", "등산"]

is_duplicate_user = user_svc.is_duplicate_user
load_users = user_svc.load_users
save_users = user_svc.save_users


def view():
    st.header("사용자 등록 / 성향 설문")
    render_demo_actions_panel("signup")
    admin_mode = st.session_state.get('admin_mode', False)
    # Admin previously had tabs for 관리; user management moved to admin dashboard.
    tabs = None

    # --- Deferred reset of survey sliders after successful save ---
    if st.session_state.pop('clear_survey_answers', False):
        for i in range(len(QUESTIONS)):
            st.session_state.pop(f"q_{i}", None)
        # also clear basic draft input widget values if any remained
        for k in ["new_name", "new_employee_number", "new_region", "new_rank", "new_interests"]:
            st.session_state.pop(k, None)

    # --- Creation Form (Tab 0 or standalone) ---
    create_container = st.container()
    with create_container:
        st.subheader("신규 사용자 등록")
        if 'new_user_draft' not in st.session_state:
            with st.form("form_basic", clear_on_submit=False):
                name = st.text_input("이름", key="new_name")
                employee_number = st.text_input(
                    "사번", key="new_employee_number")
                region = st.selectbox("지역", REGION_OPTIONS, key="new_region")
                rank = st.selectbox("직급", RANK_OPTIONS, key="new_rank")
                interests = st.multiselect(
                    "관심사", INTEREST_OPTIONS, key="new_interests")
                next_step = st.form_submit_button("다음 ➜ 성향 설문")
                if next_step:
                    if not (name and employee_number and interests):
                        st.error("이름, 사번, 관심사를 모두 입력해야 합니다.")
                    else:
                        users = load_users()
                        if is_duplicate_user(name, region, users):
                            st.error("중복 사용자 (이름+지역) 존재. 저장 취소.")
                        else:
                            st.session_state.new_user_draft = {
                                'name': name,
                                'employee_number': employee_number,
                                'region': region,
                                'rank': rank,
                                'interests': interests,
                            }
                            st.success("기본 정보가 임시 저장되었습니다. 성향 설문을 완료하세요.")
                            st.rerun()
        else:
            draft = st.session_state.new_user_draft
            st.info(
                f"기본 정보 저장됨: {draft['name']} / {draft['region']} / {draft['rank']}")
            if st.button("◀ 기본 정보 수정"):
                del st.session_state.new_user_draft
                st.rerun()
            with st.form("form_survey", clear_on_submit=False):
                st.markdown("### 성향 설문")
                answers: list[int] = []
                for i, q in enumerate(QUESTIONS):
                    default_val = st.session_state.get(f"q_{i}", 3)
                    answer = st.slider(q, 1, 5, int(default_val), key=f"q_{i}")
                    answers.append(answer)
                finish = st.form_submit_button("최종 저장")
                if finish:
                    personality_trait = classify_personality(answers)
                    uid = create_id_with_prefix('u')
                    d = draft
                    user = User(id=uid, name=d['name'], employee_number=d['employee_number'], region=d['region'], rank=d['rank'],
                                interests=d['interests'], personality_trait=personality_trait, survey_answers=answers)
                    user_svc.append_user(user)
                    st.session_state.current_user_id = uid
                    # cleanup
                    del st.session_state.new_user_draft
                    for k in ["new_name", "new_employee_number", "new_interests"]:
                        st.session_state[k] = "" if k != "new_interests" else [
                        ]
                    # mark survey answers for clearing on next script run to avoid modifying widget state post-instantiation
                    st.session_state.clear_survey_answers = True
                    st.success(f"저장 완료: {d['name']} (성향: {personality_trait})")
                    st.rerun()

    # All user list/edit/delete logic moved to Admin Dashboard (사용자 관리 탭)
