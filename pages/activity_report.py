import streamlit as st
from services import activity, persistence
from typing import Dict, Any

def _club_options():
    """Returns a list of active clubs for the selectbox."""
    clubs_all = persistence.load_list('clubs')
    active_clubs = [c for c in clubs_all if c.get('status') == 'Active']
    if not active_clubs:
        return []

    # Create a user map to get leader names for display
    users = persistence.load_list('users')
    user_map = {u['id']: u for u in users}

    options = []
    for c in active_clubs:
        leader_id = c.get('leader_id')
        leader_name = user_map.get(leader_id, {}).get('name', 'N/A')
        options.append(f"{c['id']} - {leader_name} 팀")
    return options

def view():
    """Renders the activity report submission page."""
    st.header("활동 보고서 제출")

    club_options = _club_options()
    if not club_options:
        st.warning("활동 보고서를 제출할 수 있는 'Active' 상태의 클럽이 없습니다. 어드민에게 문의하세요.")
    else:
        choice = st.selectbox("클럽 선택", options=club_options)
        club_id = choice.split()[0]

        with st.form("activity_report_form", clear_on_submit=True):
            date = st.date_input("활동 날짜")
            raw_text = st.text_area("활동 내용")
            photo = st.file_uploader("사진 업로드 (시뮬레이션)")
            part_count = st.number_input("참여 인원(선택)", min_value=0, max_value=100, value=0)

            submitted = st.form_submit_button("보고서 제출")
            if submitted:
                if not raw_text:
                    st.error("활동 내용을 입력해주세요.")
                else:
                    photo_name = photo.name if photo is not None else 'no_photo'
                    rep = activity.create_activity_report(
                        club_id=club_id,
                        date=str(date),
                        photo_name=photo_name,
                        raw_text=raw_text,
                        participant_override=part_count if part_count > 0 else None,
                    )
                    st.success(f"보고서 생성 완료. ID: {rep.id}")

    st.divider()
    st.subheader("내가 제출한 보고서")
    reports = activity.list_reports()
    if reports:
        # A simple filter could be added here later if a user login system is implemented
        st.dataframe(reports, use_container_width=True)
    else:
        st.caption("아직 제출한 보고서가 없습니다.")