import streamlit as st
from typing import Dict, Any

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
    leader_name = user_map.get(club.get('leader_id'), {}).get('name', 'N/A')

    with st.container(border=True):
        st.subheader(f"Club: {leader_name}'s Team")

        c1, c2, c3 = st.columns(3)
        c1.metric("Status", club.get('status', 'N/A'))
        c2.metric("Members", len(club.get('member_ids', [])))
        c3.metric("Points", points)

        member_names = [user_map.get(mid, {}).get('name', '?') for mid in club.get('member_ids', [])]
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