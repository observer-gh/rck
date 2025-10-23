import streamlit as st
from dataclasses import asdict
import time  # may not be needed if unconditional rerun kept; left for potential future debounce


def _seed_nemo_cohort(region: str):
    """Seed base demo user (nemo if demo_user absent) + 4 peers sharing '영화보기'.

    If a user with id 'demo_user' exists, that user is treated as the base and we do NOT create 'nemo'.
    Otherwise we create 'nemo'. Always attempts to add 4 peers (nemo_peer*/demo_peer*). Returns list of created names.
    Idempotent for already existing peer names.
    """
    from services import persistence
    from services.survey import QUESTIONS, classify_personality
    from domain.models import User
    from utils.ids import create_id_with_prefix
    import random
    users_existing = persistence.load_list('users')
    created = []
    demo_central = next(
        (u for u in users_existing if u.get('id') == 'demo_user'), None)
    base_used_demo_user = demo_central is not None
    # create nemo only if no demo_user and nemo absent
    if not base_used_demo_user and not any(u.get('name') == 'nemo' for u in users_existing):
        nemo_answers = [2] * len(QUESTIONS)
        nemo_trait = classify_personality(nemo_answers)
        nemo_user = User(
            id=create_id_with_prefix('u'),
            name='nemo',
            employee_number='AUTO-NEMO',
            region=region,
            rank='사원',
            interests=['축구', '영화보기'],
            personality_trait=nemo_trait,
            survey_answers=nemo_answers
        )
        users_existing.append(asdict(nemo_user))
        created.append('nemo')
    # peers
    INTEREST_OPTIONS = ["축구", "영화보기", "보드게임",
                        "러닝", "독서", "헬스", "요리", "사진", "등산"]
    base_pool = [i for i in INTEREST_OPTIONS if i != '영화보기']
    from services.survey import QUESTIONS as Q2  # reuse len in case of import diffs
    RANK_OPTIONS = ["사원", "대리", "과장", "차장", "부장"]
    for idx in range(1, 5):
        name_peer = f"{'demo_peer' if base_used_demo_user else 'nemo_peer'}{idx}"
        if any(u.get('name') == name_peer for u in users_existing):
            continue
        extra_count = random.randint(1, 3)
        extras = random.sample(base_pool, extra_count)
        peer_interests = ['영화보기'] + extras
        peer_answers = [random.randint(1, 3) for _ in range(len(Q2))]
        peer_trait = classify_personality(peer_answers)
        peer_user = User(
            id=create_id_with_prefix('u'),
            name=name_peer,
            employee_number=f"AUTO-P{idx}",
            region=region,
            rank=random.choice(RANK_OPTIONS),
            interests=peer_interests,
            personality_trait=peer_trait,
            survey_answers=peer_answers
        )
        users_existing.append(asdict(peer_user))
        created.append(name_peer)
    if created:
        persistence.replace_all('users', users_existing)
    return created


def render_demo_sidebar(context: str = ""):
    """Sidebar component aggregating demo utilities (seeding, status, quick solo club, auto-seed/match).

    Always visible; buttons conditionally enabled depending on current demo state.
    Fixes prior double-click issue by avoiding unnecessary manual reruns.
    """
    from services import persistence
    from utils.ids import create_id_with_prefix
    from domain.models import MatchRun, User
    from services import matching
    from demo import sample_data
    import datetime as _dt
    st.sidebar.markdown("#### 🧪 Demo")
    users = persistence.load_list('users')
    clubs = persistence.load_list('clubs')
    demo_cluster = [u for u in users if u.get('name') == 'nemo' or str(
        u.get('name', '')).startswith('nemo_peer')]
    demo_count = len(demo_cluster)
    st.sidebar.write(f"nemo cohort: {demo_count}/5")
    # Region fallback from existing demo_user or nemo else 서울
    raw_region = next((u.get('region')
                      for u in users if u.get('id') == 'demo_user'), None)
    if not raw_region:
        raw_region = next((u.get('region')
                          for u in users if u.get('name') == 'nemo'), '서울')
    region = raw_region if isinstance(raw_region, str) and raw_region else '서울'
    if 'demo_seed_done' not in st.session_state:
        st.session_state.demo_seed_done = demo_count >= 5
    seed_disabled = st.session_state.demo_seed_done or demo_count >= 5
    col_seed, col_reset = st.sidebar.columns(2)
    with col_seed:
        if st.button("Seed", key="btn_seed_nemo", disabled=seed_disabled):
            created = _seed_nemo_cohort(region)
            if created:
                st.session_state.demo_seed_done = True
                st.sidebar.success("Seeded")
            else:
                st.sidebar.info("Already")
            st.rerun()
    with col_reset:
        if st.button("Reset", key="btn_demo_wipe_simple"):
            from services import persistence as _p
            for _k in ['users', 'clubs', 'match_runs', 'activity_reports']:
                _p.replace_all(_k, [])
            st.session_state.pop('current_user_id', None)
            st.session_state.pop('demo_seed_done', None)
            st.success("Cleared")
            st.rerun()
    # Solo demo club (for current user if demo_user)
    current_user_id = getattr(st.session_state, 'current_user_id', None)
    if current_user_id == 'demo_user':
        only_demo_user = len(users) == 1 and users[0].get('id') == 'demo_user'
        has_club = any(
            c for c in clubs if current_user_id in c.get('member_ids', []))
        if st.sidebar.button("Solo 데모 클럽", key="btn_demo_solo", disabled=has_club, help="demo_user 1인 클럽"):
            if not has_club:
                from datetime import datetime, timezone
                club_id = create_id_with_prefix('club')
                now_iso = datetime.now(
                    timezone.utc).isoformat().replace('+00:00', 'Z')
                demo_club = {
                    'id': club_id,
                    'member_ids': [current_user_id],
                    'leader_id': current_user_id,
                    'name': 'Demo Solo Club',
                    'primary_interest': '축구',
                    'status': 'Active',
                    'chat_link': '',
                    'match_score_breakdown': {},
                    'explanations': {},
                    'match_run_id': None,
                    'created_at': now_iso,
                    'updated_at': now_iso,
                }
                clubs.append(demo_club)
                persistence.replace_all('clubs', clubs)
                st.sidebar.success("Solo 클럽 생성 완료")
                st.rerun()
        auto_disabled = not only_demo_user
        if st.sidebar.button("9명 자동생성+매칭", key="btn_demo_autoseed_match", disabled=auto_disabled, help="demo_user만 존재할 때 실행"):
            if only_demo_user:
                from dataclasses import asdict as _asdict
                new_users = [_asdict(u) for u in sample_data.make_users(9)]
                users_all = users + new_users
                persistence.replace_all('users', users_all)
                from domain.models import user_from_dict
                user_objs = [user_from_dict(u) for u in users_all]
                run_id = create_id_with_prefix('run')
                clubs_new = matching.compute_matches(
                    user_objs, target_size=5, run_id=run_id)
                clubs_dicts = [_asdict(c) for c in clubs_new]
                existing_clubs = persistence.load_list('clubs')
                existing_clubs.extend(clubs_dicts)
                persistence.replace_all('clubs', existing_clubs)
                runs = persistence.load_list('match_runs')
                run_meta = MatchRun(id=run_id, created_at=_dt.datetime.now(_dt.timezone.utc).isoformat().replace(
                    '+00:00', 'Z'), target_size=5, user_count=len(users_all), club_count=len(clubs_dicts))
                runs.append(_asdict(run_meta))
                persistence.replace_all('match_runs', runs)
                st.sidebar.success(f"자동생성+매칭 완료 (Run {run_id})")
                st.rerun()
    st.sidebar.markdown("---")


def render_demo_actions_panel(context: str = ""):
    """Render a demo-only action panel (solo club create + auto-seed/match) for the demo user.

    Shown when current session user is 'demo_user'. If there are already >1 users or any clubs, panel is still shown
    but auto-seed button is disabled (provides feedback) to guide the demo narrative.
    """
    from services import persistence
    current_user_id = getattr(st.session_state, 'current_user_id', None)
    if current_user_id != 'demo_user':
        return
    users = persistence.load_list('users')
    clubs = persistence.load_list('clubs')
    only_demo_user = len(users) == 1 and users[0].get('id') == 'demo_user'
    has_any_club = any(True for _c in clubs)
    st.markdown(
        "<div style='border:1px dashed #888; padding:0.85rem; border-radius:6px; background:#fafafa; margin-top:0.5rem;'>"
        f"<strong>🧪 데모 전용 영역</strong> <small style='color:#666'>(context: {context or 'global'})</small><br/>"
        "두 가지 버튼으로 빠르게 시연 흐름을 만들 수 있습니다. ① 1인 클럽 생성 ② 동료 자동 생성 & 매칭 실행."
        "</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("1) 데모 클럽 만들기", key=f"demo_make_club_{context}"):
            from utils.ids import create_id_with_prefix
            from datetime import datetime, timezone
            if not any(c for c in clubs if current_user_id in c.get('member_ids', [])):
                club_id = create_id_with_prefix('club')
                now_iso = datetime.now(
                    timezone.utc).isoformat().replace('+00:00', 'Z')
                demo_club = {
                    'id': club_id,
                    'member_ids': [current_user_id],
                    'leader_id': current_user_id,
                    'name': 'Demo Solo Club',
                    'primary_interest': '축구',
                    'status': 'Active',
                    'chat_link': '',
                    'match_score_breakdown': {},
                    'explanations': {},
                    'match_run_id': None,
                    'created_at': now_iso,
                    'updated_at': now_iso,
                }
                clubs.append(demo_club)
                persistence.replace_all('clubs', clubs)
                st.success("데모 클럽이 생성되었습니다.")
                st.rerun()
            else:
                st.info("이미 클럽이 존재하여 새 1인 데모 클럽 생성을 건너뜁니다.")
    with col2:
        disabled = not only_demo_user
        help_text = None if only_demo_user else "데모 사용자만 존재할 때만 자동 생성 가능합니다."
        if st.button("2) 동료 9명 자동생성 → 매칭", key=f"demo_autoseed_{context}", disabled=disabled, help=help_text):
            from dataclasses import asdict
            from services import matching
            from demo import sample_data
            from domain.models import User, MatchRun
            from utils.ids import create_id_with_prefix
            import datetime as _dt
            # Safety re-check
            users = persistence.load_list('users')
            if not (len(users) == 1 and users[0].get('id') == 'demo_user'):
                st.error("조건이 충족되지 않아 실행을 취소했습니다.")
            else:
                new_users = [asdict(u) for u in sample_data.make_users(9)]
                users_all = users + new_users
                persistence.replace_all('users', users_all)
                from domain.models import user_from_dict
                user_objs = [user_from_dict(u) for u in users_all]
                run_id = create_id_with_prefix('run')
                clubs_new = matching.compute_matches(
                    user_objs, target_size=5, run_id=run_id)
                clubs_dicts = [asdict(c) for c in clubs_new]
                existing_clubs = persistence.load_list('clubs')
                existing_clubs.extend(clubs_dicts)
                persistence.replace_all('clubs', existing_clubs)
                runs = persistence.load_list('match_runs')
                run_meta = MatchRun(id=run_id, created_at=_dt.datetime.now(_dt.timezone.utc).isoformat().replace(
                    '+00:00', 'Z'), target_size=5, user_count=len(users_all), club_count=len(clubs_dicts))
                runs.append(asdict(run_meta))
                persistence.replace_all('match_runs', runs)
                st.success(
                    f"자동 생성 및 매칭 완료! Run ID: {run_id} | 생성된 클럽 {len(clubs_dicts)}")
                st.balloons()
                st.rerun()


def render_demo_sidebar_floating(context: str = ""):
    """Floating overlay demo tools inside sidebar using absolute positioning.

    Provides quick actions & status without pushing navigation down. Keys namespaced to avoid collisions.
    Falls back to inline if CSS positioning unsupported (mobile narrow width).
    """
    from services import persistence
    from utils.ids import create_id_with_prefix
    from domain.models import MatchRun, User
    from services import matching
    from demo import sample_data
    import datetime as _dt
    # Inject CSS for floating panel
    st.sidebar.markdown(
        """
        <style>
        div[data-testid="stSidebar"] { position: relative; }
        .demo-floating-box { position: absolute; top: 60px; left: 8px; right: 8px; z-index: 50;
            background: rgba(255,255,255,0.92); border:1px solid #DDD; border-radius:10px; padding:0.6rem 0.7rem;
            box-shadow:0 2px 6px rgba(0,0,0,0.08); backdrop-filter: blur(3px); }
        .demo-floating-box h4 { margin:0 0 0.35rem 0; font-size:0.9rem; }
        .demo-floating-box .small { font-size:0.65rem; color:#666; }
        @media (max-width: 800px){ .demo-floating-box { position: static; margin-bottom:0.75rem; } }
        </style>
        """, unsafe_allow_html=True)
    users = persistence.load_list('users')
    clubs = persistence.load_list('clubs')
    demo_cluster = [u for u in users if u.get('name') == 'nemo' or str(
        u.get('name', '')).startswith('nemo_peer')]
    demo_count = len(demo_cluster)
    raw_region = next((u.get('region')
                      for u in users if u.get('id') == 'demo_user'), None)
    if not raw_region:
        raw_region = next((u.get('region')
                          for u in users if u.get('name') == 'nemo'), '서울')
    region = raw_region if isinstance(raw_region, str) and raw_region else '서울'
    if 'demo_seed_done' not in st.session_state:
        st.session_state.demo_seed_done = demo_count >= 5
    seed_disabled = st.session_state.demo_seed_done or demo_count >= 5
    box = st.sidebar.container()
    with box:
        st.markdown('<div class="demo-floating-box">', unsafe_allow_html=True)
        st.markdown(
            f"<h4>🧪 Demo Cohort</h4><div class='small'>Context: {context or 'global'}</div>", unsafe_allow_html=True)
        st.progress(min(demo_count, 5)/5.0)
        st.caption(f"nemo peers: {demo_count}/5")
        if st.button("Seed nemo", key="float_seed_nemo", disabled=seed_disabled, help="Create nemo + 4 peers"):
            created = _seed_nemo_cohort(region)
            if created:
                st.session_state.demo_seed_done = True
                st.success("✔ 생성")
                st.rerun()
            else:
                st.info("이미 존재")
        current_user_id = getattr(st.session_state, 'current_user_id', None)
        if current_user_id == 'demo_user':
            only_demo_user = len(users) == 1 and users[0].get(
                'id') == 'demo_user'
            has_club = any(
                c for c in clubs if current_user_id in c.get('member_ids', []))
            if st.button("Solo 클럽", key="float_demo_solo", disabled=has_club):
                if not has_club:
                    from datetime import datetime, timezone
                    club_id = create_id_with_prefix('club')
                    now_iso = datetime.now(
                        timezone.utc).isoformat().replace('+00:00', 'Z')
                    demo_club = {'id': club_id, 'member_ids': [current_user_id], 'leader_id': current_user_id, 'name': 'Demo Solo Club', 'primary_interest': '축구',
                                 'status': 'Active', 'chat_link': '', 'match_score_breakdown': {}, 'explanations': {}, 'match_run_id': None, 'created_at': now_iso, 'updated_at': now_iso}
                    clubs.append(demo_club)
                    persistence.replace_all('clubs', clubs)
                    st.success("Solo 생성")
                    st.rerun()
            auto_disabled = not only_demo_user
            if st.button("9명 자동+매칭", key="float_autoseed_match", disabled=auto_disabled):
                if only_demo_user:
                    from dataclasses import asdict as _asdict
                    new_users = [_asdict(u) for u in sample_data.make_users(9)]
                    users_all = users + new_users
                    persistence.replace_all('users', users_all)
                    user_objs = [User(**u) for u in users_all]
                    run_id = create_id_with_prefix('run')
                    clubs_new = matching.compute_matches(
                        user_objs, target_size=5, run_id=run_id)
                    clubs_dicts = [_asdict(c) for c in clubs_new]
                    existing_clubs = persistence.load_list('clubs')
                    existing_clubs.extend(clubs_dicts)
                    persistence.replace_all('clubs', existing_clubs)
                    runs = persistence.load_list('match_runs')
                    run_meta = MatchRun(id=run_id, created_at=_dt.datetime.now(_dt.timezone.utc).isoformat().replace(
                        '+00:00', 'Z'), target_size=5, user_count=len(users_all), club_count=len(clubs_dicts))
                    runs.append(_asdict(run_meta))
                    persistence.replace_all('match_runs', runs)
                    st.success("매칭 완료")
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
