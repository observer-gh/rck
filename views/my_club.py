import streamlit as st
from services import persistence
from typing import Dict
from ui.components import club_card, styled_member_chips


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
    # Small inline demo match button
    match_clicked = st.button(
        "매칭 실행", help="데모용 빠른 매칭: 고정 데모 클럽 제외하고 나머지 사용자 매칭")
    if match_clicked:
        from services import matching
        from domain.models import user_from_dict, MatchRun
        from utils.ids import create_id_with_prefix
        import datetime as _dt
        from dataclasses import asdict as _asdict
        from domain.models import Club
        users_all = persistence.load_list('users')
        # Identify fixed demo club members (demo_user + demo_peer1..4)
        demo_ids = {u.get('id') for u in users_all if u.get(
            'id') == 'demo_user' or str(u.get('name', '')).startswith('demo_peer')}
        clubs_existing = persistence.load_list('clubs')
        # Create fixed demo club if full cohort (demo_user + 4 peers) exists and not yet created
        have_full_set = 'demo_user' in demo_ids and len(
            [d for d in demo_ids if str(d).startswith('demo_peer')]) >= 4
        already_fixed = any('demo_user' in c.get('member_ids', []) and len([m for m in c.get(
            'member_ids', []) if str(m).startswith('demo_peer')]) >= 4 for c in clubs_existing)
        if have_full_set and not already_fixed:
            peer_ids_raw = [u.get('id') for u in users_all if str(
                u.get('name', '')).startswith('demo_peer')][:4]
            peer_ids = [str(pid)
                        for pid in peer_ids_raw if isinstance(pid, str)]
            member_ids: list[str] = ['demo_user'] + peer_ids
            fixed_club = Club(
                id=create_id_with_prefix('club'),
                name="데모 고정 팀 (영화보기)",
                member_ids=member_ids,
                leader_id='demo_user',
                primary_interest='영화보기',
                status='Active',
                match_run_id=None
            )
            explanation = "매칭 실행 시 생성된 고정 데모 팀"
            fixed_club.explanations = {
                mid: {"그룹": explanation} for mid in member_ids}
            fixed_club.match_score_breakdown = {}
            clubs_existing.append(_asdict(fixed_club))
            persistence.replace_all('clubs', clubs_existing)
        fixed_members = set()
        for c in clubs_existing:
            mids = set(c.get('member_ids', []))
            if 'demo_user' in mids and len([m for m in mids if str(m).startswith('demo_peer')]) >= 4:
                fixed_members = mids
                break
        # Exclude fixed members from new matching pass
        remaining_users = [user_from_dict(
            u) for u in users_all if u.get('id') not in fixed_members]
        if len(remaining_users) < 5:
            st.warning("매칭에 필요한 최소 5명 미만입니다 (고정 데모 클럽 제외). 전체 사용자로 재시도합니다.")
            remaining_users = [user_from_dict(u) for u in users_all]
        if len(remaining_users) >= 5:
            run_id = create_id_with_prefix('run')
            new_clubs = matching.compute_matches(
                remaining_users, target_size=5, run_id=run_id)
            # Normalize status Active
            new_club_dicts = []
            for c in new_clubs:
                cd = _asdict(c)
                cd['status'] = cd.get('status') or 'Active'
                new_club_dicts.append(cd)
            clubs_existing.extend(new_club_dicts)
            persistence.replace_all('clubs', clubs_existing)
            runs = persistence.load_list('match_runs')
            run_meta = MatchRun(id=run_id, created_at=_dt.datetime.now(_dt.timezone.utc).isoformat().replace(
                '+00:00', 'Z'), target_size=5, user_count=len(remaining_users), club_count=len(new_club_dicts))
            runs.append(_asdict(run_meta))
            persistence.replace_all('match_runs', runs)
            st.success(f"매칭 완료: {len(new_club_dicts)} 클럽 생성 (Run {run_id})")
            st.rerun()
        else:
            st.error("사용자가 너무 적어 매칭을 수행할 수 없습니다.")
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
        'member_ids', []) and c.get('status') in ('Active', 'Matched')]
    if not user_clubs:
        st.info("아직 배정된 (활성) 클럽이 없습니다.")
        st.write("관리자가 매칭을 실행하고 클럽을 활성화하면 이곳에 표시됩니다.")
        return

    def _ts(club: dict):
        return club.get('updated_at') or club.get('created_at') or ''
    my_club = sorted(user_clubs, key=_ts, reverse=True)[0]
    user_map = _user_map()
    pts_map = _club_points_map()
    club_card(my_club, user_map, pts_map.get(
        my_club['id'], 0), current_user_id=current_user_id)
    styled_member_chips(my_club['member_ids'],
                        user_map, current_user_id=current_user_id)
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
