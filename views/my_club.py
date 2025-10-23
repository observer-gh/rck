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
    # Match Clubs button (moved from demo sidebar)
    if st.button("Match Clubs", help="고정 데모 클럽 생성 후 나머지 사용자 매칭"):
        from services import persistence as _p
        from services import matching
        from domain.models import user_from_dict, MatchRun, Club
        from utils.ids import create_id_with_prefix
        from dataclasses import asdict as _asdict
        import datetime as _dt
        users_all = _p.load_list('users')
        # Ensure fixed demo peers exist
        from ui.components.demo import _seed_demo_peers  # reuse existing logic
        # pick region from existing demo_user or default 서울
        demo_region_raw = next(
            (u.get('region') for u in users_all if u.get('id') == 'demo_user'), '서울')
        demo_region = demo_region_raw if isinstance(
            demo_region_raw, str) and demo_region_raw else '서울'
        _seed_demo_peers(demo_region)
        users_all = _p.load_list('users')
        clubs_existing = _p.load_list('clubs')
        # Detect fixed demo club
        fixed_members = []
        for c in clubs_existing:
            mids = c.get('member_ids', [])
            if 'demo_user' in mids and len([m for m in mids if str(m).startswith('demo_peer')]) >= 5:
                fixed_members = mids
                break
        if not fixed_members:
            demo_user_rec = next((u for u in users_all if u.get(
                'id') == 'demo_user' or u.get('name') == '데모사용자'), None)
            peer_ids = [u.get('id') for u in users_all if str(
                u.get('name', '')).startswith('demo_peer')][:5]
            if demo_user_rec and len(peer_ids) == 5:
                fixed_members = [demo_user_rec['id']] + peer_ids
                fixed_club = Club(
                    id=create_id_with_prefix('club'),
                    name=f"{demo_user_rec.get('region', '서울')} 축구 · 데모 팀",
                    member_ids=fixed_members,
                    leader_id=demo_user_rec['id'],
                    primary_interest='축구',
                    status='Active'
                )
                fc_dict = _asdict(fixed_club)
                fc_dict['is_demo_fixed'] = True
                fc_dict['explanations'] = {
                    mid: {"그룹": "고정 데모 팀"} for mid in fixed_members}
                clubs_existing.append(fc_dict)
                _p.replace_all('clubs', clubs_existing)
        # Prepare remaining users for matching
        remaining_users = [user_from_dict(
            u) for u in users_all if u.get('id') not in fixed_members]
        if len(remaining_users) < 5:
            st.warning("매칭에 필요한 인원이 부족하여 전체 사용자 대상으로 재시도합니다.")
            remaining_users = [user_from_dict(u) for u in users_all]
        if len(remaining_users) >= 5:
            run_id = create_id_with_prefix('run')
            new_clubs = matching.compute_matches(
                remaining_users, target_size=5, run_id=run_id)
            new_cd = []
            for c in new_clubs:
                d = _asdict(c)
                d['status'] = d.get('status') or 'Active'
                new_cd.append(d)
            clubs_existing.extend(new_cd)
            _p.replace_all('clubs', clubs_existing)
            runs = _p.load_list('match_runs')
            run_meta = MatchRun(id=run_id, created_at=_dt.datetime.now(_dt.timezone.utc).isoformat().replace(
                '+00:00', 'Z'), target_size=5, user_count=len(remaining_users), club_count=len(new_cd))
            runs.append(_asdict(run_meta))
            _p.replace_all('match_runs', runs)
            st.success(f"매칭 완료: {len(new_cd)} 클럽 생성 (Run {run_id})")
            st.rerun()
        else:
            st.error("매칭을 수행하기 위한 사용자가 부족합니다.")
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
    # Legacy per-user explanation expander removed for streamlined demo view.
