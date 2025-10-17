import streamlit as st

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
            from services import sample_data, matching
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
                user_objs = [User(**u) for u in users_all]
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