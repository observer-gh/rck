import streamlit as st
from dataclasses import asdict
import time  # may not be needed if unconditional rerun kept; left for potential future debounce


def _seed_demo_peers(region: str):
    """Deterministically ensure demo peers demo_peer1..4 exist.

    NOTE: Previously this function also created a fixed demo club automatically.
    That side-effect has been removed so that club formation only occurs when
    the user explicitly triggers matching (e.g. via '매칭 실행' on the 내 클럽 page).
    """
    from services import persistence
    from services.survey import classify_personality
    from domain.models import User, Club
    from utils.ids import create_id_with_prefix

    users_existing = persistence.load_list('users')
    created = []
    # Define deterministic peers
    peer_defs = [
        {"idx": 1, "rank": "사원", "nickname": "alpha", "interests": [
            "영화보기", "보드게임", "독서"], "answers": [2, 2, 2, 2, 2, 2, 2]},
        {"idx": 2, "rank": "대리", "nickname": "bravo", "interests": [
            "영화보기", "축구", "러닝"], "answers": [3, 2, 2, 2, 2, 2, 2]},
        {"idx": 3, "rank": "과장", "nickname": "charlie", "interests": [
            "영화보기", "헬스", "요리"], "answers": [2, 3, 2, 2, 2, 2, 2]},
        {"idx": 4, "rank": "차장", "nickname": "delta", "interests": [
            "영화보기", "사진", "등산"], "answers": [2, 2, 3, 2, 2, 2, 2]},
    ]
    for pd in peer_defs:
        name_peer = f"demo_peer{pd['idx']}"
        if any(u.get('name') == name_peer for u in users_existing):
            continue
        trait = classify_personality(pd['answers'])
        peer_user = User(
            id=create_id_with_prefix('u'),
            name=name_peer,
            employee_number=f"DEMO-P{pd['idx']}",
            region=region,
            rank=pd['rank'],
            interests=pd['interests'],
            personality_trait=trait,
            survey_answers=pd['answers'],
            nickname=pd.get('nickname')
        )
        users_existing.append(asdict(peer_user))
        created.append(name_peer)
    if created:
        persistence.replace_all('users', users_existing)

    return created


def _seed_all_demo_users(region: str):
    """Ensure demo peers + add up to 25 extra demo auto users."""
    from services import persistence
    from services.survey import QUESTIONS, classify_personality
    from domain.models import User
    from utils.ids import create_id_with_prefix
    import random
    users = persistence.load_list('users')
    # First seed base cohort
    base_created = _seed_demo_peers(region)
    users = persistence.load_list('users')  # refresh
    existing_names = {u.get('name') for u in users}
    INTERESTS = ["축구", "영화보기", "보드게임", "러닝", "독서", "헬스", "요리", "사진", "등산"]
    NICK_POOL = ["jet", "luna", "moss", "orbit", "pixel",
                 "quill", "ray", "sage", "terra", "vega", "wren", "zephyr"]
    RANKS = ["사원", "대리", "과장", "차장", "부장"]
    REGIONS = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
               "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]
    extra_created = 0
    for i in range(1, 26):
        name = f"auto25_{i}"
        if name in existing_names:
            continue
        interests = random.sample(INTERESTS, k=random.randint(2, 4))
        answers = [random.choice([1, 2, 3]) for _ in range(len(QUESTIONS))]
        trait = classify_personality(answers)
        nickname = NICK_POOL[(i - 1) % len(NICK_POOL)]
        u = User(id=create_id_with_prefix('u'), name=name, employee_number=f"AUTO25-{i:02}",
                 region=random.choice(REGIONS), rank=random.choice(RANKS), interests=interests,
                 personality_trait=trait, survey_answers=answers, nickname=nickname)
        users.append(asdict(u))
        existing_names.add(name)
        extra_created += 1
    if extra_created:
        persistence.replace_all('users', users)
    return len(base_created), extra_created


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
    st.sidebar.markdown("<div style='font-size:11px; padding:4px 8px; background:#f5f7fa; border:1px solid #d0d7e2; border-radius:6px; display:inline-block; margin-bottom:6px;'>✏️ 데모 전용 영역</div>", unsafe_allow_html=True)
    users = persistence.load_list('users')
    clubs = persistence.load_list('clubs')
    demo_cluster = [u for u in users if u.get('id') == 'demo_user' or str(
        u.get('name', '')).startswith('demo_peer')]
    demo_count = len(demo_cluster)
    st.sidebar.write(f"demo cohort: {demo_count}/5")
    # Region fallback from existing demo_user or nemo else 서울
    raw_region = next((u.get('region')
                      for u in users if u.get('id') == 'demo_user'), None)
    if not raw_region:
        raw_region = next((u.get('region')
                          for u in users if u.get('name') == 'nemo'), '서울')
    region = raw_region if isinstance(raw_region, str) and raw_region else '서울'
    if 'demo_seed_done' not in st.session_state:
        st.session_state.demo_seed_done = demo_count >= 5
    seed_disabled = st.session_state.demo_seed_done and demo_count >= 5
    from domain.constants import DEMO_USER
    col_seed, col_match, col_reset = st.sidebar.columns(3)
    with col_seed:
        if st.button("Seed", key="btn_seed_all", disabled=seed_disabled, help="데모 사용자(+존재시 skip) + 고정 4 peers + 추가 25 랜덤"):
            users_local = persistence.load_list('users')
            # Ensure canonical demo_user or accept manually created one named 데모사용자
            has_canonical = any(
                u.get('id') == 'demo_user' for u in users_local)
            has_named_demo = any(u.get('name') == '데모사용자' for u in users_local)
            if not has_canonical:
                if has_named_demo:
                    # Skip creating canonical; treat named demo as baseline
                    pass
                else:
                    users_local.append(DEMO_USER.copy())
                    persistence.replace_all('users', users_local)
            # Seed fixed peers + fixed club
            _seed_demo_peers(region)
            # Add 25 random users (excluding any existing names)
            from services.survey import QUESTIONS, classify_personality
            from domain.models import User
            from dataclasses import asdict as _asdict
            import random
            users_local = persistence.load_list('users')  # refresh after peers
            existing_names = {u.get('name') for u in users_local}
            INTERESTS = ["축구", "영화보기", "보드게임",
                         "러닝", "독서", "헬스", "요리", "사진", "등산"]
            RANKS = ["사원", "대리", "과장", "차장", "부장"]
            REGIONS = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
                       "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]
            added = 0
            for i in range(1, 26):
                name = f"auto25_{i}"
                if name in existing_names:
                    continue
                interests = random.sample(INTERESTS, k=random.randint(2, 4))
                answers = [random.choice([1, 2, 3])
                           for _ in range(len(QUESTIONS))]
                trait = classify_personality(answers)
                from utils.ids import create_id_with_prefix
                u = User(id=create_id_with_prefix('u'), name=name, employee_number=f"AUTO25-{i:02}",
                         region=random.choice(REGIONS), rank=random.choice(RANKS), interests=interests,
                         personality_trait=trait, survey_answers=answers)
                users_local.append(_asdict(u))
                existing_names.add(name)
                added += 1
            if added:
                persistence.replace_all('users', users_local)
            # Update state
            users_local = persistence.load_list('users')
            demo_cluster = [u for u in users_local if u.get('id') == 'demo_user' or str(
                u.get('name', '')).startswith('demo_peer') or u.get('name') == '데모사용자']
            st.session_state.demo_seed_done = len(demo_cluster) >= 5
            st.sidebar.success(f"Seed 완료: peers 확보 + 추가 {added}명")
            st.rerun()
    with col_match:
        from domain.models import user_from_dict
        if st.button("Match Clubs", key="btn_match_clubs", disabled=len(users) < 5, help="고정 데모 클럽 + 나머지 매칭"):
            users_all = persistence.load_list('users')
            # Ensure fixed club exists; _seed_demo_peers already does this, but re-run to be safe
            _seed_demo_peers(region)
            users_all = persistence.load_list('users')
            clubs_existing = persistence.load_list('clubs')
            fixed_member_ids = []
            # Find existing fixed club (leader demo_user and contains 4 peers)
            for c in clubs_existing:
                if c.get('leader_id') in ['demo_user'] or any(str(n).startswith('demo_peer') for n in c.get('member_ids', [])):
                    peers = [m for m in c.get('member_ids', []) if str(
                        m).startswith('demo_peer')]
                    if 'demo_user' in c.get('member_ids', []) and len(peers) >= 4:
                        fixed_member_ids = c.get('member_ids', [])
                        break
            if not fixed_member_ids:
                # Attempt to construct manually if missing
                demo_user_rec = next(
                    (u for u in users_all if u.get('id') == 'demo_user'), None)
                peer_ids = [u.get('id') for u in users_all if str(
                    u.get('name', '')).startswith('demo_peer')][:4]
                if demo_user_rec and len(peer_ids) == 4:
                    fixed_member_ids = [demo_user_rec['id']] + peer_ids
            # Prepare users excluding fixed members for algorithmic matching
            algo_users = [user_from_dict(u) for u in users_all if u.get(
                'id') not in fixed_member_ids]
            run_id = create_id_with_prefix('run')
            clubs_new = matching.compute_matches(
                algo_users, target_size=5, run_id=run_id)
            clubs_dicts = []
            for c in clubs_new:
                cd = asdict(c)
                cd['status'] = cd.get('status') or 'Active'
                clubs_dicts.append(cd)
            existing_clubs = persistence.load_list('clubs')
            existing_clubs.extend(clubs_dicts)
            persistence.replace_all('clubs', existing_clubs)
            runs = persistence.load_list('match_runs')
            run_meta = MatchRun(id=run_id, created_at=_dt.datetime.now(_dt.timezone.utc).isoformat().replace(
                '+00:00', 'Z'), target_size=5, user_count=len(users_all), club_count=len(clubs_dicts))
            runs.append(asdict(run_meta))
            persistence.replace_all('match_runs', runs)
            st.sidebar.success(
                f"추가 매칭 완료: {len(clubs_dicts)} 클럽 (Run {run_id})")
            st.session_state.nav_target = "👥 내 클럽"
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
    # Removed legacy auto-seed+match button; consolidated in Seed + Match Clubs flows.
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
    # Deprecated: function disabled. Use render_demo_sidebar instead.
    return None
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
    # demo cohort now defined as demo_user + demo_peer1..4; legacy 'nemo' removed
    demo_cluster = [u for u in users if u.get('id') == 'demo_user' or str(
        u.get('name', '')).startswith('demo_peer')]
    demo_count = len(demo_cluster)
    raw_region = next((u.get('region')
                      for u in users if u.get('id') == 'demo_user'), None)
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
        st.caption(f"demo peers: {demo_count}/5")
        if st.button("Seed demo peers", key="float_seed_demo", disabled=seed_disabled, help="Create demo_peer1..4"):
            created = _seed_demo_peers(region)
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
