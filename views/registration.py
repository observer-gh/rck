import streamlit as st
from services import users as user_svc
from domain.constants import get_demo_user, save_demo_user
from domain.models import User
from utils.ids import create_id_with_prefix
from services.survey import classify_personality
from dataclasses import asdict
from ui.components import user_form

def view():
    st.header("사용자 등록 / 성향 설문")

    users = user_svc.load_users()

    # Determine if the registration form should be locked.
    is_first_visit = 'signup_first_visit' not in st.session_state
    if is_first_visit:
        st.session_state.signup_first_visit = True

    demo_only_context = len(users) == 1 and users[0].get('id') == 'demo_user'
    registration_locked = 'current_user_id' in st.session_state and not (st.session_state.signup_first_visit and demo_only_context)

    if registration_locked:
        st.info("이미 등록된 사용자가 있습니다. 폼은 읽기 전용 상태입니다.")
        if st.button("내 프로필로 이동 ▶"):
            st.session_state.signup_first_visit = False
            st.session_state.nav_target = "🙍 내 프로필"
            st.rerun()
        return

    # Render the unified user form
    default_user_data = get_demo_user()
    new_user_data = user_form.render(default_user_data, key_prefix="signup", is_new=True)

    if new_user_data:
        name = new_user_data['name']
        region = new_user_data['region']

        is_dup = user_svc.is_duplicate_user(name, region, users)
        allow_demo_dup = name == '데모사용자'

        if is_dup and not allow_demo_dup:
            st.error("중복 사용자 (이름+지역) 존재. 저장 취소.")
        else:
            personality_trait = classify_personality(new_user_data['survey_answers'])

            # Check if we should update the demo user or create a new one
            demo_user = get_demo_user()
            is_demo_update = (
                (len(users) == 1 and users[0]['id'] == 'demo_user') or
                (name == demo_user.get('name') or new_user_data['employee_number'] == demo_user.get('employee_number'))
            )

            if is_demo_update:
                user_to_update = next((u for u in users if u['id'] == 'demo_user'), None)
                if user_to_update:
                    user_to_update.update({
                        **new_user_data,
                        'personality_trait': personality_trait
                    })
                    save_demo_user(user_to_update)
                    st.session_state.current_user_id = 'demo_user'
                    st.success(f"데모 사용자 업데이트 완료: {name} (성향: {personality_trait})")

            else:
                new_user = User(
                    id=create_id_with_prefix('u'),
                    name=name,
                    nickname=new_user_data['nickname'],
                    employee_number=new_user_data['employee_number'],
                    region=region,
                    rank=new_user_data['rank'],
                    interests=new_user_data['interests'],
                    personality_trait=personality_trait,
                    survey_answers=new_user_data['survey_answers']
                )
                users.append(asdict(new_user))
                st.session_state.current_user_id = new_user.id
                st.success(f"가입 완료: {name} (성향: {personality_trait})")

            user_svc.save_users(users)

            # Post-registration cleanup and navigation
            st.session_state.nav_target = "🙍 내 프로필"
            st.session_state.focus_anchor = 'app-top'
            st.session_state.signup_first_visit = False

            # Clear form fields for the next potential user
            for k in st.session_state.keys():
                if k.startswith("signup_"):
                    del st.session_state[k]

            st.rerun()
