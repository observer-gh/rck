import streamlit as st
from typing import Dict, Any
from services import users as user_svc
from services.survey import QUESTIONS, classify_personality
from domain.constants import REGIONS, RANKS, INTERESTS

is_duplicate_user = user_svc.is_duplicate_user
load_users = user_svc.load_users
save_users = user_svc.save_users


def _profile_block(user: Dict[str, Any]):
    # Deprecated summary block intentionally left empty (removed per requirements)
    pass


def view():
    st.header("내 프로필")
    users = load_users()
    current_user_id = st.session_state.get('current_user_id')
    if not current_user_id:
        st.info("선택/생성된 사용자가 없습니다. 먼저 사용자 등록을 완료하세요.")
        return
    me = next((u for u in users if u['id'] == current_user_id), None)
    if not me:
        st.warning("세션 사용자 ID로 사용자를 찾을 수 없습니다. 다시 등록이 필요할 수 있습니다.")
        return
    # Summary block removed; editing section shown directly.
    st.subheader("프로필 수정")
    with st.form(f"edit_self_{current_user_id}"):
        new_name = st.text_input("이름", value=me.get('name', ''))
        new_employee_number = st.text_input(
            "사번", value=me.get('employee_number', ''))
        raw_region = me.get('region')
        raw_rank = me.get('rank')
        region_val: str = raw_region if isinstance(
            raw_region, str) and raw_region in REGIONS else REGIONS[0]
        rank_val: str = raw_rank if isinstance(
            raw_rank, str) and raw_rank in RANKS else RANKS[0]
        new_region = st.selectbox(
            "지역", REGIONS, index=REGIONS.index(region_val))
        new_rank = st.selectbox(
            "직급", RANKS, index=RANKS.index(rank_val))
        new_interests = st.multiselect(
            "관심사", INTERESTS, default=me.get('interests', []))
        existing_answers = me.get('survey_answers') or []
        # normalize legacy 5-point answers to 3-point by mapping: 1-2 ->1, 3 ->2, 4-5 ->3
        norm_answers = []
        for v in existing_answers:
            if isinstance(v, int):
                if v <= 2:
                    norm_answers.append(1)
                elif v == 3:
                    norm_answers.append(2)
                else:
                    norm_answers.append(3)
            else:
                norm_answers.append(2)
        # Pad/truncate
        if len(norm_answers) < len(QUESTIONS):
            norm_answers += [2] * (len(QUESTIONS) - len(norm_answers))
        elif len(norm_answers) > len(QUESTIONS):
            norm_answers = norm_answers[:len(QUESTIONS)]
        OPTION_MAP = {"아니요": 1, "중간": 2, "네": 3}
        labels = list(OPTION_MAP.keys())
        reverse_map = {v: k for k, v in OPTION_MAP.items()}
        new_answers = []
        for i, q in enumerate(QUESTIONS):
            initial_label = reverse_map.get(norm_answers[i], "중간")
            choice = st.radio(f"{i+1}. {q}", labels, key=f"self_edit_q_{current_user_id}_{i}",
                              index=labels.index(initial_label), horizontal=True)
            new_answers.append(OPTION_MAP[choice])
        submitted = st.form_submit_button("저장")
        if submitted:
            safe_name = new_name or ""
            safe_region = new_region or ""
            if is_duplicate_user(safe_name, safe_region, users, exclude_id=current_user_id):
                st.error("중복 사용자 (이름+지역) 존재. 변경 취소.")
            else:
                me.update({
                    'name': safe_name,
                    'employee_number': new_employee_number,
                    'region': safe_region,
                    'rank': new_rank,
                    'interests': new_interests,
                    'personality_trait': classify_personality(new_answers),
                    'survey_answers': new_answers
                })
                save_users(users)
                st.success("업데이트 완료")
                st.rerun()
