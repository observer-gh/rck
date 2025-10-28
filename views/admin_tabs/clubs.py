import streamlit as st
import time

from services import persistence, admin as admin_svc
from utils.explanations import build_ai_match_explanation


def render_clubs_tab():
    """Displays all clubs, filterable by match run, and allows activation."""
    st.subheader("📊 클럽 관리")

    clubs_all = persistence.load_list('clubs')
    if not clubs_all:
        st.info("생성된 클럽이 없습니다.")
        return

    # UI for selecting a match run to view.
    runs_meta = persistence.load_list('match_runs')
    run_order = {r['id']: i + 1 for i,
                 r in enumerate(sorted(runs_meta, key=lambda r: r['created_at']))}
    run_ids = sorted({c.get('match_run_id', '')
                     for c in clubs_all if c.get('match_run_id')}, reverse=True)

    if run_ids:
        label_map = {
            f"Run #{run_order.get(r['id'], '?')}: {r['created_at'].replace('T', ' ')[:16]} | size {r['target_size']} | clubs {r['club_count']}": r['id']
            for r in runs_meta if r['id'] in run_ids
        }
        sel_label = st.selectbox(
            "표시할 Match Run 선택", options=list(label_map.keys()))
        clubs_to_display = [c for c in clubs_all if c.get(
            'match_run_id') == label_map[sel_label]]
    else:
        st.warning("Run ID가 없는 클럽만 존재합니다. 전체를 표시합니다.")
        clubs_to_display = clubs_all

    points_map = admin_svc.get_club_points_map()
    user_map = admin_svc.get_user_map()

    st.caption(f"표시된 클럽 수: {len(clubs_to_display)}")

    # Display each club in an expander.
    modified = False
    # Prioritize demo club (containing demo_user with name '데모사용자' or id demo_user) at top

    def _is_demo_club(c):
        mids = c.get('member_ids', [])
        return ('demo_user' in mids)
    # Stable sort: demo clubs first, preserve relative order otherwise
    clubs_sorted = sorted(clubs_to_display, key=lambda c: (
        0 if _is_demo_club(c) else 1))
    for idx, c in enumerate(clubs_sorted, start=1):
        pts = points_map.get(c['id'], 0)
        # Prefer persisted semantic name; fallback to generic numbered label.
        display_name = c.get('name') or f"클럽 #{idx}"
        # Render status as Active if nemo/demo_user is a member (display-only override)
        members_ids = c.get('member_ids', []) or []
        raw_status = c.get('status', 'N/A')
        status_disp = 'Active' if 'demo_user' in members_ids else raw_status
        display_name = display_name + \
            ' (demo)' if 'demo_user' in members_ids else display_name
        club_title = f"{display_name} | 인원 {len(members_ids)} | 상태: {status_disp} | 포인트: {pts}"

        with st.expander(club_title):
            leader_name = admin_svc.get_user_name(c['leader_id'], user_map)
            member_names = [admin_svc.get_user_name(
                mid, user_map) for mid in c['member_ids']]
            # Display-only cleanup: strip 'det_extra_' prefix for readability.

            def _display_name(n: str):
                return n[len("det_extra_"):] if isinstance(n, str) and n.startswith("det_extra_") else n
            leader_disp = _display_name(leader_name)
            members_disp = [_display_name(n) for n in member_names]
            # Map user IDs to employee numbers for display augmentation.
            emp_map = {u['id']: u.get('employee_number', '') for u in admin_svc.get_user_map(
            ).values()} if hasattr(admin_svc, 'get_user_map') else {}
            leader_emp = emp_map.get(c['leader_id'], '')
            leader_full = f"{leader_disp} ({leader_emp})" if leader_emp else leader_disp
            members_full = [f"{n} ({emp_map.get(mid, '')})" if emp_map.get(
                mid, '') else n for n, mid in zip(members_disp, c['member_ids'])]
            st.write(f"**리더:** {leader_full}")
            st.write(f"**멤버:** {', '.join(members_full)}")

            # AI Explanation Section (admin view parity with legacy fallback)
            member_ids = c.get('member_ids', []) or []
            if member_ids:
                try:
                    expl = build_ai_match_explanation(c, user_map)
                    with st.expander("AI 매칭 설명", expanded=False):
                        st.markdown(f"**요약:** {expl['summary']}")
                        for b in expl['bullets']:
                            st.markdown(f"- {b}")
                        if expl.get('narrative'):
                            st.markdown(
                                f"<div style='margin-top:8px;padding:10px;border-left:3px solid #4a90e2;background:#f5f9ff;border-radius:4px;font-size:13px;'>{expl['narrative']}</div>",
                                unsafe_allow_html=True
                            )
                        if st.checkbox("멤버별 상세 보기", key=f"ai_member_details_{c['id']}"):
                            for line in expl.get('member_details', []):
                                st.markdown(f"  * {line}")
                except Exception as e:
                    st.caption(f"AI 설명 생성 실패: {e}")

            # Activation / Deactivation UI
            club_status = c.get('status')
            if club_status == 'Matched':
                leader_input = st.text_input(
                    "리더 이름 확인", key=f"leader_check_{c['id']}", help=f"'{leader_disp}'을(를) 입력하세요.")
                if leader_input.strip() == leader_disp:
                    chat_url = st.text_input(
                        "채팅 링크 (선택)", key=f"chat_{c['id']}")
                    if st.button("클럽 활성화", key=f"activate_{c['id']}"):
                        admin_svc.activate_club(c['id'], chat_url, clubs_all)
                        modified = True
            elif club_status == 'Active':
                if st.button("비활성화", key=f"deactivate_{c['id']}"):
                    # Revert to Matched state (retain chat_link, but could clear if desired)
                    c['status'] = 'Matched'
                    c['updated_at'] = admin_svc.utc_now_iso() if hasattr(
                        admin_svc, 'utc_now_iso') else c.get('updated_at')
                    persistence.replace_all('clubs', clubs_all)
                    st.info("클럽이 비활성화(Matched) 상태로 되돌려졌습니다.")
                    st.rerun()

    if modified:
        st.success("클럽 상태 변경사항이 저장되었습니다.")
        st.rerun()
