import streamlit as st

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