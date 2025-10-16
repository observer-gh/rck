import streamlit as st
from services import activity, persistence


def _club_options(current_user_id: str | None):
    clubs_all = persistence.load_list('clubs')
    active_clubs = [c for c in clubs_all if c.get('status') == 'Active']
    if not active_clubs:
        return []
    users = persistence.load_list('users')
    user_map = {u['id']: u for u in users}
    # If user context exists, limit to their clubs
    if current_user_id:
        active_clubs = [
            c for c in active_clubs if current_user_id in c.get('member_ids', [])]
    options = []
    for c in active_clubs:
        leader_id = c.get('leader_id')
        leader_name = user_map.get(leader_id, {}).get('name', 'N/A')
        options.append(f"{c['id']} - {leader_name} 팀")
    return options


def view():
    st.header("활동 보고서 제출")
    current_user_id = getattr(st.session_state, 'current_user_id', None)
    club_options = _club_options(current_user_id)
    if not club_options:
        st.warning("활동 보고서를 제출할 수 있는 'Active' 상태의 (내) 클럽이 없습니다.")
    else:
        choice = st.selectbox("클럽 선택", options=club_options)
        if not choice:
            st.stop()
        club_id = str(choice).split()[0]
        with st.form("activity_report_form", clear_on_submit=True):
            date = st.date_input("활동 날짜")
            raw_text = st.text_area("활동 내용")
            photo = st.file_uploader("사진 업로드 (시뮬레이션)")
            part_count = st.number_input(
                "참여 인원(선택)", min_value=0, max_value=100, value=0)
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
        # Filter to reports from user's clubs if user context exists
        if current_user_id:
            user_club_ids = {c['id'] for c in persistence.load_list(
                'clubs') if current_user_id in c.get('member_ids', [])}
            reports = [r for r in reports if r['club_id'] in user_club_ids]
        st.dataframe(reports, use_container_width=True)
    else:
        st.caption("아직 제출한 보고서가 없습니다.")
