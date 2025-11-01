import streamlit as st
from typing import Dict, Any, Optional
from domain.constants import REGIONS, RANKS, INTERESTS
from services.survey import QUESTIONS

def render(user_data: Dict[str, Any], key_prefix: str, is_new: bool = False):
    """
    Renders a reusable user form for both registration and profile editing.

    Args:
        user_data (Dict[str, Any]): The user data to populate the form with.
        key_prefix (str): A unique prefix for Streamlit widget keys.
        is_new (bool): Flag to adjust labels for the registration context.

    Returns:
        Dict[str, Any]: The updated user data from the form, or None if not submitted.
    """
    with st.form(f"form_{key_prefix}"):
        st.subheader("1단계: 기본 정보" if is_new else "기본 정보")

        name = st.text_input("이름", value=user_data.get('name', ''), key=f"{key_prefix}_name")
        nickname = st.text_input("닉네임", value=user_data.get('nickname', ''), key=f"{key_prefix}_nickname")
        employee_number = st.text_input("사번", value=user_data.get('employee_number', ''), key=f"{key_prefix}_employee_number")

        region_idx = REGIONS.index(user_data['region']) if user_data.get('region') in REGIONS else 0
        region = st.selectbox("지역", REGIONS, index=region_idx, key=f"{key_prefix}_region")

        rank_idx = RANKS.index(user_data['rank']) if user_data.get('rank') in RANKS else 0
        rank = st.selectbox("직급", RANKS, index=rank_idx, key=f"{key_prefix}_rank")

        interests = st.multiselect("관심사", INTERESTS, default=user_data.get('interests', []), key=f"{key_prefix}_interests")

        st.subheader("2단계: 성향 설문" if is_new else "성향 설문")

        OPTION_MAP = {"아니요": 1, "중간": 2, "네": 3}
        option_labels = list(OPTION_MAP.keys())
        reverse_map = {v: k for k, v in OPTION_MAP.items()}

        answers = []
        survey_answers = user_data.get('survey_answers', [])
        for i, q in enumerate(QUESTIONS):
            # Get the stored answer, default to 2 ('중간')
            answer_val = survey_answers[i] if i < len(survey_answers) else 2
            initial_label = reverse_map.get(answer_val, "중간")
            choice = st.radio(
                f"{i+1}. {q}",
                option_labels,
                key=f"{key_prefix}_q_{i}",
                index=option_labels.index(initial_label),
                horizontal=True
            )
            answers.append(OPTION_MAP[choice])

        submit_label = "다음 ➜ 성향 설문" if is_new else "저장"
        submitted = st.form_submit_button(submit_label)

        if submitted:
            # Basic validation
            if not (name and employee_number and interests):
                st.error("이름, 사번, 관심사를 모두 입력해야 합니다.")
                return None
            if not (employee_number.isdigit() and len(employee_number) == 8):
                st.error("사번은 8자리 숫자여야 합니다 (예: 10150000).")
                return None

            return {
                'name': name,
                'nickname': nickname,
                'employee_number': employee_number,
                'region': region,
                'rank': rank,
                'interests': interests,
                'survey_answers': answers
            }

    return None
