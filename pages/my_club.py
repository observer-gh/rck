import streamlit as st
from services import persistence
from typing import Dict, Any

def _user_map():
    """Helper to create a user ID to user object mapping."""
    return {u['id']: u for u in persistence.load_list('users')}

def _club_points_map() -> Dict[str, int]:
    """Helper to calculate total verified points for each club."""
    reports = persistence.load_list('activity_reports')
    pts: Dict[str, int] = {}
    for r in reports:
        if r.get('status') == 'Verified':
            pts[r['club_id']] = pts.get(r['club_id'], 0) + int(r.get('points_awarded', 0))
    return pts

def view():
    """
    Renders the page for a user to see their assigned club.

    This is a simplified view. It currently just shows the first active club found.
    A real implementation would require a logged-in user context.
    """
    st.header("내 클럽 정보")

    # In a real app, we'd get the current user's ID from session state.
    # For this demo, we'll just find the first user and see if they are in a club.
    # This is a placeholder for demonstration purposes.
    users = persistence.load_list('users')
    if not users:
        st.warning("등록된 사용자가 없습니다. 먼저 프로필을 등록해주세요.")
        return

    # Simulate finding the user's club. We'll just find the first active club for anyone.
    clubs_all = persistence.load_list('clubs')
    active_clubs = [c for c in clubs_all if c.get('status') == 'Active']

    if not active_clubs:
        st.info("아직 배정된 클럽이 없습니다.", icon="ℹ️")
        st.write("프로필을 등록하고 관리자가 클럽 매칭을 실행하면, 여기에 소속 클럽 정보가 표시됩니다.")
        st.write("아직 프로필을 등록하지 않으셨다면, '프로필/설문' 메뉴에서 등록을 완료해주세요.")
        return

    # For the demo, just display the details of the first active club found.
    my_club = active_clubs[0]
    user_map = _user_map()
    pts_map = _club_points_map()

    st.subheader(f"클럽: {user_map.get(my_club['leader_id'], {}).get('name', 'N/A')} 팀")

    col1, col2, col3 = st.columns(3)
    col1.metric("클럽 상태", my_club.get('status', 'N/A'))
    col2.metric("총 인원", len(my_club['member_ids']))
    col3.metric("누적 포인트", pts_map.get(my_club['id'], 0))

    if my_club.get('chat_link'):
        st.link_button("그룹 채팅방 바로가기", my_club['chat_link'])

    st.write("---")

    leader_name = user_map.get(my_club['leader_id'], {}).get('name', 'Unknown')
    member_names = [user_map.get(mid, {}).get('name', 'Unknown') for mid in my_club['member_ids']]

    st.write(f"**리더:** {leader_name}")
    st.write(f"**멤버:** {', '.join(member_names)}")

    with st.expander("매칭 점수 상세"):
        st.json(my_club['match_score_breakdown'])

    exp = my_club.get('explanations')
    if exp:
        with st.expander("매칭 설명 (AI 분석)"):
            for uid, peers in exp.items():
                uname = user_map.get(uid, {}).get('name', 'Unknown')
                rendered = '; '.join(f"{user_map.get(pid, {}).get('name', '?')}:{reason}" for pid, reason in peers.items())
                st.write(f"**{uname}**: {rendered}")