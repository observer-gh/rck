import streamlit as st
from services import persistence
from domain.models import User
from utils.ids import create_id_with_prefix
from services.survey import QUESTIONS, classify_personality
from dataclasses import asdict
from typing import Optional, List, Dict, Any

REGION_OPTIONS = [
    "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
    "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"
]
RANK_OPTIONS = ["사원", "대리", "과장", "차장", "부장"]
INTEREST_OPTIONS = ["축구", "영화보기", "보드게임", "러닝", "독서", "헬스", "요리", "사진", "등산"]


def is_duplicate_user(name: str, region: str, users: List[Dict[str, Any]], exclude_id: Optional[str] = None) -> bool:
    name_norm = (name or '').strip().lower()
    region_norm = (region or '').strip().lower()
    for u in users:
        if exclude_id and u['id'] == exclude_id:
            continue
        if u.get('name', '').strip().lower() == name_norm and u.get('region', '').strip().lower() == region_norm:
            return True
    return False


def load_users():
    return persistence.load_list('users')


def save_users(users):
    persistence.replace_all('users', users)


def view():
    st.header("사용자 등록 / 성향 설문")
    # Demo actions panel removed; all demo buttons reside in sidebar only.

    # Deferred survey slider cleanup if flagged
    if st.session_state.pop('clear_survey_answers', False):
        for i in range(len(QUESTIONS)):
            st.session_state.pop(f"q_{i}", None)
        for k in ["new_name", "new_employee_number", "new_region", "new_rank", "new_interests"]:
            st.session_state.pop(k, None)

    users = load_users()

    # Determine first-visit behavior: allow demo user scenario to appear as fresh
    if 'signup_first_visit' not in st.session_state:
        st.session_state.signup_first_visit = True
    existing_current = st.session_state.get('current_user_id')
    demo_only_context = len(users) == 1 and (
        users[0].get('id') == 'demo_user' or users[0].get('name') == '데모사용자')
    base_locked = bool(
        existing_current and 'new_user_draft' not in st.session_state)
    registration_locked = base_locked and not (
        st.session_state.signup_first_visit and demo_only_context)
    if registration_locked:
        st.info("이미 등록된 사용자가 있습니다. 폼은 읽기 전용 상태입니다.")
        if st.button("내 프로필로 이동 ▶"):
            st.session_state.signup_first_visit = False
            st.session_state.nav_target = "🙍 내 프로필"
            st.rerun()

    # Step 1: Basic info form if draft not present
    if 'new_user_draft' not in st.session_state:
        # Determine default demo-based values
        demo_base = next(
            (u for u in users if u.get('id') == 'demo_user'), None)
        if not demo_base:
            demo_base = next(
                (u for u in users if u.get('name') == 'nemo'), None)
        # Default name always "데모사용자" for convenience (user can change)
        default_name = "데모사용자"
        # Fixed default employee number irrespective of demo_base
        default_emp = '10150000'
        reg_val = demo_base.get('region') if demo_base else None
        default_region = reg_val if isinstance(
            reg_val, str) and reg_val in REGION_OPTIONS else REGION_OPTIONS[0]
        # Rank default: demo base rank if valid else '사원'
        # Fixed default rank
        default_rank = '사원'
        ints_val = demo_base.get('interests') if demo_base else []
        # 관심사 기본값: 데모 사용자/네모의 관심사 없으면 대표 2개 자동 선택
        default_interests = ints_val if isinstance(
            ints_val, list) and ints_val else ["축구", "영화보기"]
        with st.form("form_basic", clear_on_submit=False):
            st.subheader("1단계: 기본 정보")
            name = st.text_input("이름", key="new_name", value=default_name)
            # Nickname: show previously typed, existing demo base nickname, or fallback 'nemo'
            existing_nick = st.session_state.get('new_nickname')
            base_nick = (demo_base.get('nickname')
                         if demo_base else None) or 'nemo'
            nickname_val = existing_nick if existing_nick not in (
                None, '') else base_nick
            nickname = st.text_input(
                "닉네임", key="new_nickname", value=nickname_val, help="프로필에 표시될 짧은 핸들. 미입력 시 자동 생성.")
            employee_number = st.text_input(
                "사번", key="new_employee_number", value=default_emp, placeholder="8자리 숫자 (예: 10150000)")
            region = st.selectbox(
                "지역", REGION_OPTIONS, key="new_region", index=REGION_OPTIONS.index(default_region))
            rank = st.selectbox("직급", RANK_OPTIONS, key="new_rank",
                                index=RANK_OPTIONS.index(default_rank))
            interests = st.multiselect(
                "관심사", INTEREST_OPTIONS, key="new_interests", default=default_interests)
            next_step = st.form_submit_button(
                "다음 ➜ 성향 설문", disabled=registration_locked)
            if next_step and not registration_locked:
                def _emp_valid(v: str) -> bool:
                    return v.isdigit() and len(v) == 8
                if not (name and employee_number and interests):
                    st.error("이름, 사번, 관심사를 모두 입력해야 합니다.")
                elif not _emp_valid(employee_number):
                    st.error("사번은 8자리 숫자여야 합니다 (예: 10150000).")
                else:
                    is_dup = is_duplicate_user(name, region, users)
                    allow_demo_dup = name == '데모사용자'
                    if is_dup and not allow_demo_dup:
                        st.error("중복 사용자 (이름+지역) 존재. 저장 취소.")
                    else:
                        st.session_state.new_user_draft = {
                            'name': name,
                            'nickname': nickname.strip() if nickname else '',
                            'employee_number': employee_number,
                            'region': region,
                            'rank': rank,
                            'interests': interests,
                        }
                        st.session_state.signup_first_visit = False
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
            st.subheader("2단계: 성향 설문")
            OPTION_MAP = {"아니요": 1, "중간": 2, "네": 3}
            option_labels = list(OPTION_MAP.keys())
            answers: List[int] = []
            # sanitize legacy stored values "잘 모르겠다" -> "중간"
            for i in range(len(QUESTIONS)):
                legacy_key = f"q_{i}"
                if st.session_state.get(legacy_key) == "잘 모르겠다":
                    st.session_state[legacy_key] = "중간"
            for i, q in enumerate(QUESTIONS):
                choice = st.radio(f"{i+1}. {q}", option_labels,
                                  key=f"q_{i}", index=1, horizontal=True)
                answers.append(OPTION_MAP[choice])
            finish = st.form_submit_button(
                "최종 저장", disabled=registration_locked)
            if finish and not registration_locked:
                personality_trait = classify_personality(answers)
                uid = create_id_with_prefix('u')
                d = draft
                user = User(id=uid, name=d['name'], employee_number=d['employee_number'], region=d['region'], rank=d['rank'],
                            interests=d['interests'], personality_trait=personality_trait, survey_answers=answers, nickname=d.get('nickname'))
                users.append(asdict(user))
                save_users(users)
                st.session_state.current_user_id = uid
                # Defer navigation to profile page via nav_target (handled in app before radio instantiation)
                st.session_state.nav_target = "🙍 내 프로필"
                # cleanup
                del st.session_state.new_user_draft
                # clear text fields for potential next creation
                for k in ["new_name", "new_employee_number", "new_interests"]:
                    st.session_state[k] = "" if k != "new_interests" else []
                st.session_state.clear_survey_answers = True
                st.session_state.signup_first_visit = False
                st.success(f"저장 완료: {d['name']} (성향: {personality_trait})")
                st.rerun()
