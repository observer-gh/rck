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
    # Style the Match Clubs button with a dotted border (scoped to this page)
    st.markdown(
        """
        <style>
        /* Unified dotted style for action buttons on this page */
        div.stButton > button {border:2px dotted #555 !important; background:#fff; color:#222; border-radius:12px; padding:.55rem 1.1rem; font-weight:600; font-size:.9rem;}
        div.stButton > button:hover {border-color:#222; background:#f5f7fa;}
        </style>
        """,
        unsafe_allow_html=True
    )
    # Match Clubs button (moved from demo sidebar)
    if st.button("(demo) 클럽 매칭 실행", help="고정 6명 데모 클럽 생성 + 나머지 사용자 매칭(1회 클릭)"):
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
        # Ensure canonical demo user exists before seeding peers
        if not any(u.get('id') == 'demo_user' for u in users_all):
            try:
                from domain.constants import DEMO_USER
                users_all.append(DEMO_USER.copy())
                _p.replace_all('users', users_all)
                users_all = _p.load_list('users')
            except Exception:
                pass
        _seed_demo_peers(demo_region)
        users_all = _p.load_list('users')
        clubs_existing = _p.load_list('clubs')
        # Detect or create fixed 6-member demo club using Korean peer names
        PEER_NAMES = {"김서준", "이민준", "박서연", "최지후", "정하윤"}
        demo_user_rec = next((u for u in users_all if u.get(
            'id') == 'demo_user' or u.get('name') == '데모사용자'), None)
        peer_user_recs = [u for u in users_all if u.get('name') in PEER_NAMES]
        fixed_members = []
        expected_name = f"{demo_region} 축구 클럽 A (demo)"
        for c in clubs_existing:
            mids = c.get('member_ids', []) or []
            # Detect by exact name OR by composition (demo user + 5 peers)
            comp_ok = demo_user_rec and demo_user_rec['id'] in mids and len(
                {m for m in mids if any(p['id'] == m for p in peer_user_recs)}) == 5
            name_ok = c.get('name') == expected_name
            if comp_ok or name_ok:
                fixed_members = mids
                break
        if not fixed_members and demo_user_rec and len(peer_user_recs) >= 5:
            fixed_members = [demo_user_rec['id']] + [p['id']
                                                     for p in peer_user_recs]
            fixed_club = Club(
                id=create_id_with_prefix('club'),
                name=expected_name,
                member_ids=fixed_members,
                leader_id=demo_user_rec['id'],
                primary_interest='축구',
                status='Active'
            )
            fc_dict = _asdict(fixed_club)
            fc_dict['is_demo_fixed'] = True
            fc_dict['explanations'] = {
                mid: {"그룹": "고정 데모 팀 A"} for mid in fixed_members}
            clubs_existing.append(fc_dict)
            _p.replace_all('clubs', clubs_existing)
            # Removed info bar per request (club created silently)
        # Ensure session selects demo user for immediate render
        if demo_user_rec and (getattr(st.session_state, 'current_user_id', None) not in fixed_members):
            st.session_state['current_user_id'] = demo_user_rec['id']
        # Prepare remaining users for matching
        remaining_users = [user_from_dict(
            u) for u in users_all if u.get('id') not in fixed_members]
        if len(remaining_users) < 6:
            # Removed warning bar (silent fallback to broader set)
            remaining_users = [user_from_dict(
                u) for u in users_all if u.get('id') not in fixed_members]
        if len(remaining_users) >= 6:
            run_id = create_id_with_prefix('run')
            new_clubs = matching.compute_matches(
                remaining_users, target_size=6, run_id=run_id)
            new_cd = []
            for c in new_clubs:
                d = _asdict(c)
                # Force status to Active (override any 'Matched') at creation time
                d['status'] = 'Active'
                new_cd.append(d)
            clubs_existing.extend(new_cd)
            _p.replace_all('clubs', clubs_existing)
            runs = _p.load_list('match_runs')
            run_meta = MatchRun(id=run_id, created_at=_dt.datetime.now(_dt.timezone.utc).isoformat().replace(
                '+00:00', 'Z'), target_size=6, user_count=len(remaining_users), club_count=len(new_cd))
            runs.append(_asdict(run_meta))
            _p.replace_all('match_runs', runs)
            st.success(f"매칭 완료: 새 클럽 {len(new_cd)}개 생성 (Run {run_id})")
        # Unconditional rerun to refresh view (covers both creation-only and full match cases)
        st.rerun()
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
