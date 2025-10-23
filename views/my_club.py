import streamlit as st
from services import persistence
from typing import Dict
from ui.components import club_card, styled_member_chips, render_demo_actions_panel


def _user_map():
    return {u['id']: u for u in persistence.load_list('users')}


def _club_points_map() -> Dict[str, int]:
    reports = persistence.load_list('activity_reports')
    pts: Dict[str, int] = {}
    for r in reports:
        if r.get('status') == 'Verified':
            pts[r['club_id']] = pts.get(
                r['club_id'], 0) + int(r.get('points_awarded', 0))
    return pts


def view():
    st.header("내 클럽 정보")
    render_demo_actions_panel("my_club_top")
    current_user_id = getattr(st.session_state, 'current_user_id', None)
    users = persistence.load_list('users')
    if not users:
        st.warning("등록된 사용자가 없습니다. 먼저 프로필을 등록해주세요.")
        return
    if not current_user_id:
        st.info("현재 선택된 사용자 세션이 없습니다.")
        st.write("'프로필/설문' 페이지에서 사용자를 생성하거나 선택하면 여기서 소속 클럽을 볼 수 있습니다.")
        return
    clubs_all = persistence.load_list('clubs')
    user_clubs = [c for c in clubs_all if current_user_id in c.get(
        'member_ids', []) and c.get('status') == 'Active']
    if not user_clubs:
        st.info("아직 배정된 (활성) 클럽이 없습니다.")
        if current_user_id == 'demo_user':
            render_demo_actions_panel("my_club_empty")
        else:
            st.write("관리자가 매칭을 실행하고 클럽을 활성화하면 이곳에 표시됩니다.")
        return

    def _ts(club: dict):
        return club.get('updated_at') or club.get('created_at') or ''
    my_club = sorted(user_clubs, key=_ts, reverse=True)[0]
    user_map = _user_map()
    pts_map = _club_points_map()
    club_card(my_club, user_map, pts_map.get(my_club['id'], 0))
    styled_member_chips(my_club['member_ids'], user_map)
    with st.expander("매칭 점수 상세"):
        st.json(my_club.get('match_score_breakdown', {}))
    exp = my_club.get('explanations')
    if exp:
        with st.expander("매칭 설명 (AI 분석)"):
            for uid, detail in exp.items():
                uname = user_map.get(uid, {}).get('name', 'Unknown')
                group_line = detail.get('그룹')
                summary = detail.get('요약')
                st.markdown(f"**{uname}**")
                if group_line:
                    st.caption(group_line)
                bullets = []
                for k in ["공통관심사", "직급다양성", "성향조합"]:
                    if k in detail:
                        bullets.append(f"- {k}: {detail[k]}")
                if summary:
                    bullets.append(f"- 요약: {summary}")
                st.markdown("\n".join(bullets))
