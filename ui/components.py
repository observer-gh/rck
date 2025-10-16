import streamlit as st
from typing import Dict, Any, Iterable, Optional

PRIMARY_BG = "#111827"  # dark slate fallback
PRIMARY_ACCENT = "#2563EB"  # blue-600
GREEN = "#059669"  # emerald-600
YELLOW = "#D97706"  # amber-600
RED = "#DC2626"  # red-600
GRAY_BORDER = "#1f2937"
CHIP_BG = "#374151"


def inject_base_css():
    if getattr(inject_base_css, "_applied", False):
        return
    inject_base_css._applied = True
    st.markdown(
        f"""
        <style>
        .badge {{
            display:inline-block; padding:2px 8px; border-radius:12px;
            font-size:12px; line-height:16px; font-weight:600;
            background:{CHIP_BG}; color:#F9FAFB; margin-right:4px; margin-bottom:4px;
        }}
        .badge.green {{background:{GREEN};}}
        .badge.yellow {{background:{YELLOW};}}
        .badge.red {{background:{RED};}}
        .status-pill {{padding:4px 10px; border-radius:14px; font-size:12px; font-weight:600;}}
        .status-Matched {{background:#1E3A8A; color:#F9FAFB;}}
        .status-Active {{background:{GREEN}; color:#F9FAFB;}}
        .scroll-table thead th {{position:sticky; top:0; background:#111;}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def status_badge(status: str) -> str:
    cls = "green" if status.lower() in {"active", "verified"} else "yellow"
    return f'<span class="badge {cls}">{status}</span>'


def user_badge(user: Dict[str, Any]):
    """
    Displays a compact badge with user information.
    """
    st.markdown(
        f"""
        <div style="
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 8px 12px;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        ">
            <div>
                <span style="font-weight: bold;">{user.get('name', 'N/A')}</span>
                <small style="color: #666; margin-left: 8px;">({user.get('rank', 'N/A')}, {user.get('region', 'N/A')})</small>
            </div>
            <div>
                <small style="background-color: #f0f2f6; padding: 2px 6px; border-radius: 4px;">{user.get('personality_trait', 'N/A')}</small>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def club_card(club: Dict[str, Any], user_map: Dict[str, Any], points: int):
    """
    Displays a card with detailed information about a club.
    """
    leader_id = club.get('leader_id') or ''
    leader_name = user_map.get(str(leader_id), {}).get('name', 'N/A')

    with st.container(border=True):
        st.subheader(f"Club: {leader_name}'s Team")

        c1, c2, c3 = st.columns(3)
        c1.metric("Status", club.get('status', 'N/A'))
        c2.metric("Members", len(club.get('member_ids', [])))
        c3.metric("Points", points)

        member_names = [user_map.get(mid, {}).get('name', '?')
                        for mid in club.get('member_ids', [])]
        st.write(f"**Leader:** {leader_name}")
        st.write(f"**Members:** {', '.join(member_names)}")

        if club.get('chat_link'):
            st.link_button("Go to Group Chat", club['chat_link'])


def metric_chip(label: str, value: Any, delta: str = "", delta_color: str = "normal"):
    """
    Displays a metric in a compact, chip-like format.
    """
    st.markdown(
        f"""
        <div style="
            background-color: #f0f2f6;
            border-radius: 16px;
            padding: 8px 16px;
            text-align: center;
        ">
            <div style="font-size: 0.9em; color: #555;">{label}</div>
            <div style="font-size: 1.2em; font-weight: bold;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def styled_member_chips(user_ids: Iterable[str], user_map: Dict[str, Any]):
    inject_base_css()
    chips = []
    for uid in user_ids:
        name = user_map.get(uid, {}).get("name", uid)
        initial = name[0]
        chips.append(f"<span class='badge'>{initial}</span>")
    st.markdown(" ".join(chips), unsafe_allow_html=True)


def dataframe_with_status(df, status_col: Optional[str] = None):
    import pandas as _pd
    inject_base_css()
    if df is None or df.empty:
        st.caption("표시할 데이터가 없습니다.")
        return
    if status_col and status_col in df.columns:
        df = df.copy()
        df[status_col] = df[status_col].apply(status_badge)
    st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)


def report_card(report: Dict[str, Any]):
    """Render a single activity report in a card style.

    Expects keys: id, date, status, points_awarded?, club_id, formatted_report, photo_filename?, verification_metrics?
    """
    inject_base_css()
    rid = report.get('id')
    status_html = status_badge(report.get('status', 'Pending'))
    points = report.get('points_awarded', 0)
    date = report.get('date', '?')
    club_id = report.get('club_id', '?')
    photo = report.get('photo_filename') or '—'
    summary = report.get('formatted_report', '')
    metrics = report.get('verification_metrics') or {}
    with st.container(border=True):
        top_cols = st.columns([4, 2, 2])
        with top_cols[0]:
            st.markdown(f"**{rid}**  |  {date}  |  클럽: `{club_id}`")
        with top_cols[1]:
            st.markdown(status_html, unsafe_allow_html=True)
        with top_cols[2]:
            st.metric(label="Points", value=points)
        if photo and photo not in {"no_photo", ""}:
            st.caption(f"📷 첨부사진: {photo}")
        # Collapsible full text & metrics
        with st.expander("상세 내용 / Metrics", expanded=False):
            st.markdown(summary)
            if metrics:
                mcols = st.columns(len(metrics))
                for (k, v), c in zip(metrics.items(), mcols):
                    c.metric(k, v)
        # Tiny footer actions placeholder (future: copy / delete)
        st.caption(" ")


def render_demo_actions_panel(context: str = ""):
    """Render a demo-only action panel (solo club create + auto-seed/match) for the demo user.

    Shown when current session user is 'demo_user'. If there are already >1 users or any clubs, panel is still shown
    but auto-seed button is disabled (provides feedback) to guide the demo narrative.
    """
    import streamlit as st  # local import to avoid issues if components imported outside Streamlit
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
