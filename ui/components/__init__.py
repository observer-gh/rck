"""
This package provides a collection of reusable UI components for the Streamlit application.

It is organized into several modules, each containing a specific category of components:
- `base`: Basic, general-purpose components like CSS injectors and status badges.
- `cards`: Larger, more complex components for displaying detailed information.
- `demo`: Components used exclusively for the demo functionality.

By importing the components here, we provide a single, consistent access point
for the rest of the application (`from ui import components`).
"""

from .base import (
    inject_base_css,
    status_badge,
)

from .cards import (
    user_badge,
    club_card,
    report_card,
)

from .demo import (
    render_demo_actions_panel,
)

# Deprecated components that are still here for compatibility
# In a future refactoring, these should be moved to their appropriate modules
# or removed if no longer necessary.

from typing import Dict, Any, Iterable, Optional
import streamlit as st

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