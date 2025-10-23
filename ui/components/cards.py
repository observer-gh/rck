import streamlit as st
from typing import Dict, Any, Iterable

from .base import inject_base_css, status_badge
from utils.explanations import build_ai_match_explanation
from typing import Optional


def _handle(user: Dict[str, Any], current_user_id: Optional[str] = None) -> str:
    nick = user.get('nickname') or user.get('name') or 'user'
    if current_user_id and user.get('id') == current_user_id:
        return f"{nick} (나)"
    return nick


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


def club_card(club: Dict[str, Any], user_map: Dict[str, Any], points: int, current_user_id: Optional[str] = None):
    """
    Displays a card with detailed information about a club.
    """
    leader_id = club.get('leader_id') or ''
    leader_name = _handle(user_map.get(str(leader_id), {}), current_user_id)

    with st.container(border=True):
        st.subheader(f"Club: {leader_name}'s Team")

        c1, c2, c3 = st.columns(3)
        c1.metric("Status", club.get('status', 'N/A'))
        c2.metric("Members", len(club.get('member_ids', [])))
        c3.metric("Points", points)

        member_names = [_handle(user_map.get(mid, {}), current_user_id)
                        for mid in club.get('member_ids', [])]
        st.write(f"**Leader:** {leader_name}")
        st.write(f"**Members:** {', '.join(member_names)}")
        # Display trait + primary interest summary (take leader's trait as representative)
        leader_trait = user_map.get(str(leader_id), {}).get(
            'personality_trait') or '—'
        primary_interest = club.get('primary_interest') or '—'
        st.markdown(f"**성향:** {leader_trait} | **대표 관심사:** {primary_interest}")
        # AI explanation for fixed demo cohort: use names to detect peers
        member_ids = club.get('member_ids', [])
        names = [user_map.get(mid, {}).get('name', '') for mid in member_ids]
        demo_user_present = any(
            n == '데모사용자' for n in names) or 'demo_user' in member_ids
        peer_count = sum(1 for n in names if n.startswith('demo_peer'))
        if demo_user_present and peer_count >= 4:
            expl = build_ai_match_explanation(club, user_map)
            st.markdown("### AI 매칭 설명")
            # Pastel blue container styling
            st.markdown(
                f"""
                <div style="background:#eef6ff;border:1px solid #d2e6fb;padding:14px 18px;border-radius:12px;font-size:14px;line-height:1.55;">
                    <p style="margin:0 0 8px;font-weight:600;">{expl['summary']}</p>
                    <p style="margin:0 0 6px;white-space:normal;">{' '.join(expl['bullets'])}</p>
                    <p style="margin:8px 0 0;">{expl.get('narrative', '')}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            with st.expander("매칭 멤버 상세", expanded=False):
                for line in expl.get('member_details', []):
                    st.markdown(f"- {line}")

        if club.get('chat_link'):
            st.link_button("Go to Group Chat", club['chat_link'])


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
