import streamlit as st
from services import users as user_svc
from domain.constants import get_demo_user, save_demo_user
from services.survey import classify_personality
from ui.components import user_form

def view():
    st.header("내 프로필")

    users = user_svc.load_users()
    current_user_id = st.session_state.get('current_user_id')

    if not current_user_id:
        st.info("선택/생성된 사용자가 없습니다. 먼저 사용자 등록을 완료하세요.")
        return

    me = next((u for u in users if u['id'] == current_user_id), None)
    if me and me.get('id') == 'demo_user':
        try:
            me.update(get_demo_user())
        except Exception:
            pass

    if not me:
        st.warning("세션 사용자 ID로 사용자를 찾을 수 없습니다. 다시 등록이 필요할 수 있습니다.")
        return

    st.subheader("프로필 수정")

    updated_data = user_form.render(me, key_prefix=f"edit_{current_user_id}")

    if updated_data:
        safe_name = updated_data['name'] or ""
        safe_region = updated_data['region'] or ""

        if safe_name != '데모사용자' and user_svc.is_duplicate_user(safe_name, safe_region, users, exclude_id=current_user_id):
            st.error("중복 사용자 (이름+지역) 존재. 변경 취소.")
        else:
            me.update({
                'name': safe_name,
                'nickname': (updated_data['nickname'] or '').strip(),
                'employee_number': updated_data['employee_number'],
                'region': safe_region,
                'rank': updated_data['rank'],
                'interests': updated_data['interests'],
                'personality_trait': classify_personality(updated_data['survey_answers']),
                'survey_answers': updated_data['survey_answers']
            })

            user_svc.save_users(users)

            if me.get('id') == 'demo_user':
                try:
                    save_demo_user(me)
                except Exception:
                    pass

            st.success("업데이트 완료")
            st.rerun()
