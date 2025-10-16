import streamlit as st
import time

from services import persistence, activity, admin as admin_svc
from services.survey import QUESTIONS
from ui.components import user_badge
# Note: We will be moving these constants to a centralized location in a later step.
from domain.constants import REGIONS, RANKS, INTERESTS

def view():
    """
    Renders the admin dashboard, which is organized into multiple tabs
    for different administrative functions.
    """
    st.header("어드민 대시보드")
    st.markdown("이곳에서 데이터 관리, 매칭 실행, 활동 보고서 검증 등 주요 관리 작업을 수행합니다.")

    tabs = st.tabs([
        "📈 분석 및 현황", "👤 사용자 관리", "⚙️ 매칭 실행",
        "📊 클럽 관리", "✅ 보고서 검증", "💾 데이터 관리"
    ])

    # Each tab is rendered by its own dedicated function for clarity.
    with tabs[0]:
        render_analytics_tab()
    with tabs[1]:
        render_user_management_tab()
    with tabs[2]:
        render_matching_tab()
    with tabs[3]:
        render_clubs_tab()
    with tabs[4]:
        render_verification_tab()
    with tabs[5]:
        render_data_tab()

# --- Tab Rendering Functions ---

def render_analytics_tab():
    """Displays key metrics and analytics about the system."""
    st.subheader("📈 분석 및 현황")

    # Fetch analytics from the dedicated service function.
    analytics = admin_svc.get_system_analytics()

    # Display metrics in columns.
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 사용자", analytics["total_users"])
    c2.metric("총 클럽", analytics["total_clubs"])
    c3.metric("활성 클럽", analytics["active_clubs"])
    c4.metric("매칭 실행 횟수", analytics["total_match_runs"])
    c1.metric("보고서 (대기/검증)", f"{analytics['pending_reports']}/{analytics['verified_reports']}")
    c2.metric("총 포인트 (검증)", analytics["total_points_awarded"])
    c3.metric("평균 직급 다양성", f"{analytics['avg_rank_diversity']:.2f}")
    c4.metric("평균 관심사 다양성", f"{analytics['avg_interest_variety']:.2f}")

    st.write("---")
    st.subheader("클럽 포인트 순위 Top 5")

    top_clubs = admin_svc.get_top_clubs_by_points(limit=5)
    if top_clubs:
        # Prepare data for the bar chart.
        chart_data = {
            "클럽": [c['points'] for c in top_clubs],
            "이름": [c['name'] for c in top_clubs]
        }
        st.bar_chart(chart_data, x="이름", y="클럽")
    else:
        st.caption("검증된 포인트가 있는 클럽이 없습니다.")


def render_user_management_tab():
    """Provides UI for managing users, including editing and deleting."""
    st.subheader("👤 사용자 관리")

    users = persistence.load_list('users')
    if not users:
        st.info("등록된 사용자가 없습니다.")
        return

    users.sort(key=lambda u: u['name'])
    display_map = {f"{u['name']} ({u['region']})": u['id'] for u in users}

    sel_disp = st.selectbox("사용자 선택", options=["-"] + list(display_map.keys()))
    if sel_disp == "-":
        st.markdown("---")
        st.subheader("사용자 목록")
        for u in users:
            user_badge(u)
        return

    sel_id = display_map[sel_disp]
    user = next((u for u in users if u['id'] == sel_id), None)

    if user:
        with st.expander(f"편집: {user['name']} ({user['region']})", expanded=True):
            # The user editing form fields.
            new_name = st.text_input("이름", value=user['name'], key=f"adm_edit_name_{sel_id}")
            new_emp = st.text_input("사번", value=user.get('employee_number', ''), key=f"adm_edit_emp_{sel_id}")
            new_region = st.selectbox("지역", REGIONS, index=REGIONS.index(user['region']), key=f"adm_edit_region_{sel_id}")
            new_rank = st.selectbox("직급", RANKS, index=RANKS.index(user['rank']), key=f"adm_edit_rank_{sel_id}")
            new_interests = st.multiselect("관심사", INTERESTS, default=user['interests'], key=f"adm_edit_interests_{sel_id}")

            st.markdown("**성향 설문**")
            existing_answers = user.get('survey_answers') or [3] * len(QUESTIONS)
            new_answers = [st.slider(q, 1, 5, existing_answers[i], key=f"adm_edit_q_{sel_id}_{i}") for i, q in enumerate(QUESTIONS)]

            # Action buttons
            col1, col2, col3 = st.columns(3)
            if col1.button("저장", key=f"adm_save_{sel_id}"):
                try:
                    updates = {
                        'name': new_name or "", 'employee_number': new_emp, 'region': new_region or "",
                        'rank': new_rank, 'interests': new_interests, 'survey_answers': new_answers
                    }
                    admin_svc.update_user_profile(sel_id, updates, users)
                    st.success("업데이트 완료")
                    st.rerun()
                except ValueError as e:
                    st.error(e)

            if col2.button("삭제", key=f"adm_del_{sel_id}"):
                try:
                    admin_svc.delete_user(sel_id, users)
                    st.warning("삭제됨 (매칭 재실행 필요)")
                    st.rerun()
                except ValueError as e:
                    st.error(e)

            if col3.button("현재 사용자로 설정", key=f"adm_setcur_{sel_id}"):
                st.session_state.current_user_id = sel_id
                st.success("현재 사용자 세션이 업데이트되었습니다.")


def render_matching_tab():
    """Handles UI for running the matching algorithm."""
    st.subheader("⚙️ 매칭 실행")

    users_raw = persistence.load_list('users')
    if not users_raw:
        st.warning("매칭을 실행할 사용자가 없습니다. 먼저 사용자를 등록하거나 생성해주세요.")
        return

    st.info(f"현재 등록된 총 사용자: **{len(users_raw)}명**")

    # Special path for demo user to auto-generate more data.
    if len(users_raw) == 1 and users_raw[0].get('id') == 'demo_user':
        st.warning("현재 데모 사용자 1명만 존재합니다. 아래 버튼으로 동료 9명을 자동 생성하고 즉시 매칭을 실행할 수 있습니다.")
        if st.button("동료 9명 자동생성 + 매칭 실행", type="primary"):
            try:
                run_id, count = admin_svc.generate_sample_users_and_match()
                st.success(f"자동 생성 및 매칭 완료. Run ID: {run_id}, 생성된 클럽 수: {count}")
                st.balloons()
                st.rerun()
            except ValueError as e:
                st.error(e)

    target_size = st.number_input("클럽당 인원 (기본 5)", min_value=3, max_value=10, value=5)
    st.write("---")
    st.subheader("전체 재매칭")
    st.warning("주의: 이 작업은 기존 클럽에 영향을 주지 않고 새로운 클럽들을 추가 생성합니다.")

    if st.button("매칭 실행 / 새 버전 생성"):
        try:
            run_id, count = admin_svc.run_new_matching(target_size)
            st.success(f"새 매칭 실행 완료. Run ID: {run_id}, 생성된 클럽 수: {count}")
            st.balloons()
        except ValueError as e:
            st.error(e)


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


def render_verification_tab():
    """Allows admins to verify pending activity reports."""
    st.subheader("✅ 활동 보고서 검증")

    reports = activity.list_reports()
    pending = [r for r in reports if r['status'] == 'Pending']

    if not pending:
        st.info("검증 대기 중인 보고서가 없습니다.")
    else:
        st.write(f"**{len(pending)}**개의 보고서가 검증을 기다리고 있습니다.")
        for r in pending:
            with st.expander(f"Report `{r['id']}` | Club `{r['club_id']}` | Date: {r['date']}"):
                st.text_area("내용", r['formatted_report'], height=150, disabled=True)
                if st.button("AI 검증 실행", key=f"verify_{r['id']}"):
                    with st.spinner("AI 검증 시뮬레이션 중..."):
                        time.sleep(1) # Simulate delay
                        activity.verify_report(r['id'])
                    st.success("검증 완료! 포인트가 지급되었습니다.")
                    st.rerun()

    st.divider()
    st.subheader("검증 완료된 보고서")
    verified = [r for r in reports if r['status'] == 'Verified']
    st.dataframe(verified if verified else [], use_container_width=True)


def render_data_tab():
    """Provides data management functions like export and reset."""
    st.subheader("💾 데이터 관리")

    with st.container(border=True):
        st.subheader("샘플 사용자 생성")
        if st.button("샘플 사용자 15명 생성"):
            admin_svc.add_sample_users(15)
            st.success("샘플 사용자 추가 완료!")
            st.rerun()

    with st.container(border=True):
        st.subheader("데이터 내보내기 (CSV)")
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("사용자"):
            st.download_button("다운로드: users.csv", admin_svc.export_to_csv('users'), "users.csv", "text/csv")
        if c2.button("클럽"):
            st.download_button("다운로드: clubs.csv", admin_svc.export_to_csv('clubs'), "clubs.csv", "text/csv")
        if c3.button("보고서"):
            st.download_button("다운로드: reports.csv", admin_svc.export_to_csv('activity_reports'), "reports.csv", "text/csv")
        if c4.button("매칭기록"):
            st.download_button("다운로드: runs.csv", admin_svc.export_to_csv('match_runs'), "runs.csv", "text/csv")

    with st.expander("🚨 Danger Zone: 데이터 초기화"):
        st.warning("주의: 이 작업은 모든 사용자, 클럽, 보고서, 매칭 기록을 영구적으로 삭제합니다. 되돌릴 수 없습니다.")
        if st.checkbox("위험을 인지했으며, 모든 데이터를 삭제하는 데 동의합니다."):
            if st.text_input("삭제를 원하시면 'ERASE ALL DATA'를 입력하세요.") == "ERASE ALL DATA":
                if st.button("모든 데이터 영구 삭제", type="primary"):
                    admin_svc.reset_all_data()
                    st.success("모든 애플리케이션 데이터가 삭제되었습니다 (데모사용자 제외).")
                    time.sleep(2)
                    st.rerun()