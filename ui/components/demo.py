import streamlit as st
from dataclasses import asdict
import time  # may not be needed if unconditional rerun kept; left for potential future debounce


def _seed_demo_peers(region: str):
    """Ensure 5 fixed demo peers exist with hardcoded Korean names.

    Names chosen to be common and distinct. English codes kept as nickname for reference.
    """
    from services import persistence
    from services.survey import classify_personality
    from domain.models import User, Club
    from utils.ids import create_id_with_prefix

    users_existing = persistence.load_list('users')
    created = []
    peer_defs = [
        {"name": "김서준", "rank": "사원", "nickname": "alpha", "interests": [
            "축구", "보드게임", "독서"], "answers": [2, 2, 2, 2, 2, 2, 2]},
        {"name": "이민준", "rank": "대리", "nickname": "bravo", "interests": [
            "축구", "러닝", "보드게임"], "answers": [3, 2, 2, 2, 2, 2, 2]},
        {"name": "박서연", "rank": "과장", "nickname": "charlie", "interests": [
            "축구", "헬스", "요리"], "answers": [2, 3, 2, 2, 2, 2, 2]},
        {"name": "최지후", "rank": "차장", "nickname": "delta", "interests": [
            "축구", "사진", "등산"], "answers": [2, 2, 3, 2, 2, 2, 2]},
        {"name": "정하윤", "rank": "부장", "nickname": "echo", "interests": [
            "축구", "러닝", "보드게임"], "answers": [2, 2, 2, 3, 2, 2, 2]},
    ]
    existing_names = {u.get('name') for u in users_existing}
    for pd in peer_defs:
        if pd['name'] in existing_names:
            continue
        trait = classify_personality(pd['answers'])
        peer_user = User(
            id=create_id_with_prefix('u'),
            name=pd['name'],
            employee_number=f"DEMO-{pd['name']}",  # keep unique but readable
            region=region,
            rank=pd['rank'],
            interests=pd['interests'],
            personality_trait=trait,
            survey_answers=pd['answers'],
            nickname=pd.get('nickname')
        )
        users_existing.append(asdict(peer_user))
        created.append(pd['name'])
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


def _build_deterministic_extras(count: int, region: str):
    """Build deterministic extra users whose attributes guarantee club formation.

    All users share at least one common interest ("축구") ensuring the matching
    algorithm can keep a non-empty intersection while growing each group.
    Personality alternates to create distinct (region, personality_trait) buckets
    of size >= target_size (6). Ranks cycle to improve diversity.
    Names are Korean via canonical generator so they sort to top in admin.
    """
    from domain.models import User
    from utils.ids import create_id_with_prefix
    from utils.korean_names import generate_canonical_names
    from domain.constants import RANKS

    # Interest pool (each user gets 축구 + one variant)
    interest_pool = ["영화보기", "보드게임", "러닝", "독서", "헬스", "요리", "사진", "등산"]
    # Existing names: ensure no collisions with already persisted users.
    from services import persistence as _p
    existing_users = _p.load_list('users')
    existing_names = {str(u.get('name'))
                      for u in existing_users if isinstance(u.get('name'), str)}
    # high start_index to avoid collision
    names = generate_canonical_names(
        count, existing=existing_names, start_index=1000)
    extras = []
    for i in range(count):
        personality = "외향" if (i % 2 == 0) else "내향"
        rank = RANKS[i % len(RANKS)]
        second_interest = interest_pool[i % len(interest_pool)]
        interests = ["축구", second_interest]
        # Deterministic survey answers pattern keeps classify_personality unused; set trait directly.
        answers = [3, 3, 3, 3, 3, 3, 3]
        # Numeric employee number format (e.g., 10150001, 10150002, ...)
        base_emp = 10150000
        emp_num = f"{base_emp + i + 1:08d}"  # ensure 8 digits
        u = User(
            id=create_id_with_prefix('u'),
            name=f"det_extra_{names[i]}",  # prefix for easy identification
            employee_number=emp_num,
            region=region,
            rank=rank,
            interests=interests,
            personality_trait=personality,
            survey_answers=answers,
            nickname=None
        )
        extras.append(u)
    return extras


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
    _PEER_NAMES = {"김서준", "이민준", "박서연", "최지후", "정하윤"}
    demo_cluster = [u for u in users if u.get(
        'id') == 'demo_user' or u.get('name') in _PEER_NAMES]
    demo_count = len(demo_cluster)
    st.sidebar.write(f"demo cohort: {demo_count}/6")
    # Region fallback from existing demo_user or nemo else 서울
    raw_region = next((u.get('region')
                      for u in users if u.get('id') == 'demo_user'), None)
    if not raw_region:
        raw_region = next((u.get('region')
                          for u in users if u.get('name') == 'nemo'), '서울')
    region = raw_region if isinstance(raw_region, str) and raw_region else '서울'
    if 'demo_seed_done' not in st.session_state:
        st.session_state.demo_seed_done = demo_count >= 6
    seed_disabled = st.session_state.demo_seed_done and demo_count >= 6
    from domain.constants import DEMO_USER
    # Arrange buttons in a single row: Seed | Seed Whole | Reset
    col_seed, col_whole, col_reset = st.sidebar.columns(3)
    with col_seed:
        if st.button("Seed", key="btn_seed_all", disabled=seed_disabled, help="데모 사용자(+존재시 skip) + 고정 5 peers"):
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
            # Update state
            users_local = persistence.load_list('users')
            demo_cluster = [u for u in users_local if u.get('id') == 'demo_user' or u.get(
                'name') in _PEER_NAMES or u.get('name') == '데모사용자']
            st.session_state.demo_seed_done = len(demo_cluster) >= 6
            st.sidebar.success("Seed 완료: 데모 사용자 + 5 peers")
            st.rerun()
    # Full cohort seeding button
    full_disabled = len(persistence.load_list('users')) >= 30
    with col_whole:
        if st.button("Seed Whole", key="btn_seed_whole", disabled=full_disabled, help="전체 데모 코호트(30명) 사용자만 생성 (매칭은 어드민에서 실행)"):
            users_local = persistence.load_list('users')
            # Ensure demo base cohort present (demo_user + peers)
            if not any(u.get('id') == 'demo_user' for u in users_local):
                from domain.constants import DEMO_USER as _DEMO
                users_local.append(_DEMO.copy())
                persistence.replace_all('users', users_local)
            _seed_demo_peers(region)
            users_local = persistence.load_list('users')
            # Idempotent deterministic extras creation (24 total det_extra_ users)
            existing_det = [u for u in users_local if str(u.get('name', '')).startswith('det_extra_')]
            if len(existing_det) < 24:
                need = 24 - len(existing_det)
                extras = _build_deterministic_extras(need, region)
                users_local.extend([asdict(u) for u in extras])
                persistence.replace_all('users', users_local)
            total_users = len(persistence.load_list('users'))
            st.sidebar.success(f"전체 사용자 시드 완료: 총 {total_users}명 (클럽/Run 미생성) · 매칭은 어드민 대시보드에서 실행하세요")
            st.rerun()
    # Reset button (third column)
    with col_reset:
        if st.button("Reset", key="btn_demo_wipe_simple", help="모든 데모 데이터 초기화"):
            from services import persistence as _p
            for _k in ['users', 'clubs', 'match_runs', 'activity_reports']:
                _p.replace_all(_k, [])
            st.session_state.pop('current_user_id', None)
            st.session_state.pop('demo_seed_done', None)
            st.success("데모 상태 초기화 완료")
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
    demo_cluster = [u for u in users if u.get(
        'id') == 'demo_user' or u.get('name') in _PEER_NAMES]
    demo_count = len(demo_cluster)
    raw_region = next((u.get('region')
                      for u in users if u.get('id') == 'demo_user'), None)
    region = raw_region if isinstance(raw_region, str) and raw_region else '서울'
    if 'demo_seed_done' not in st.session_state:
        st.session_state.demo_seed_done = demo_count >= 6
    seed_disabled = st.session_state.demo_seed_done or demo_count >= 6
    box = st.sidebar.container()
    with box:
        st.markdown('<div class="demo-floating-box">', unsafe_allow_html=True)
        st.markdown(
            f"<h4>🧪 Demo Cohort</h4><div class='small'>Context: {context or 'global'}</div>", unsafe_allow_html=True)
        st.progress(min(demo_count, 6)/6.0)
        st.caption(f"demo peers: {demo_count}/6")
        if st.button("Seed demo peers", key="float_seed_demo", disabled=seed_disabled, help="Create demo_peer1..5"):
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
