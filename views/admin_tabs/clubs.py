import streamlit as st

from services import persistence, admin as admin_svc

def render_clubs_tab():
    """Displays all clubs, filterable by match run, and allows activation."""
    st.subheader("📊 클럽 관리")

    clubs_all = persistence.load_list('clubs')
    if not clubs_all:
        st.info("생성된 클럽이 없습니다.")
        return

    # UI for selecting a match run to view.
    runs_meta = persistence.load_list('match_runs')
    run_order = {r['id']: i + 1 for i, r in enumerate(sorted(runs_meta, key=lambda r: r['created_at']))}
    run_ids = sorted({c.get('match_run_id', '') for c in clubs_all if c.get('match_run_id')}, reverse=True)

    if run_ids:
        label_map = {
            f"Run #{run_order.get(r['id'], '?')}: {r['created_at'].replace('T', ' ')[:16]} | size {r['target_size']} | clubs {r['club_count']}": r['id']
            for r in runs_meta if r['id'] in run_ids
        }
        sel_label = st.selectbox("표시할 Match Run 선택", options=list(label_map.keys()))
        clubs_to_display = [c for c in clubs_all if c.get('match_run_id') == label_map[sel_label]]
    else:
        st.warning("Run ID가 없는 클럽만 존재합니다. 전체를 표시합니다.")
        clubs_to_display = clubs_all

    points_map = admin_svc.get_club_points_map()
    user_map = admin_svc.get_user_map()

    st.caption(f"표시된 클럽 수: {len(clubs_to_display)}")

    # Display each club in an expander.
    modified = False
    for idx, c in enumerate(clubs_to_display, start=1):
        pts = points_map.get(c['id'], 0)
        club_title = f"클럽 #{idx} | 인원 {len(c['member_ids'])} | 상태: {c.get('status', 'N/A')} | 포인트: {pts}"

        with st.expander(club_title):
            leader_name = admin_svc.get_user_name(c['leader_id'], user_map)
            member_names = [admin_svc.get_user_name(mid, user_map) for mid in c['member_ids']]
            st.write(f"**리더:** {leader_name}")
            st.write(f"**멤버:** {', '.join(member_names)}")

            # UI for activating a newly matched club.
            if c.get('status') == 'Matched':
                leader_input = st.text_input("리더 이름 확인", key=f"leader_check_{c['id']}", help=f"'{leader_name}'을(를) 입력하세요.")
                if leader_input.strip() == leader_name:
                    chat_url = st.text_input("채팅 링크 (선택)", key=f"chat_{c['id']}")
                    if st.button("클럽 활성화", key=f"activate_{c['id']}"):
                        admin_svc.activate_club(c['id'], chat_url, clubs_all)
                        modified = True

    if modified:
        st.success("클럽 상태 변경사항이 저장되었습니다.")
        st.rerun()