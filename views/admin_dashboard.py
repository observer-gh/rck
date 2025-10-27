import streamlit as st
from services import persistence, activity, matching
from demo import sample_data  # updated path for sample data generation
from domain.models import User, MatchRun
from utils.ids import create_id_with_prefix
from dataclasses import asdict
import datetime as dt
import time
import csv
import io


def _user_map():
    return {u['id']: u for u in persistence.load_list('users')}


def _user_name(uid, user_map):
    u = user_map.get(uid)
    return u['name'] if u else uid


@st.cache_data(ttl=30)
def _club_points_map():
    """Compute verified points per club (cached briefly for snappy UI)."""
    reports = persistence.load_list('activity_reports')
    pts: dict[str, int] = {}
    for r in reports:
        if r.get('status') == 'Verified':
            pts[r['club_id']] = pts.get(
                r['club_id'], 0) + int(r.get('points_awarded', 0))
    return pts


def utc_now_iso():
    return dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z')


def view():
    st.header("어드민 대시보드")
    st.markdown("주요 관리 작업을 한 곳에서 빠르게 수행하고 시스템 상태를 살펴봅니다.")

    # Separate 사용자 관리 and 매칭 실행 tabs
    tabs = st.tabs([
        "📈 분석 및 현황", "👥 사용자 관리", "⚙️ 매칭 실행", "📊 클럽 관리", "✅ 보고서 검증", "💾 데이터 관리"
    ])
    # Lazy import of tab renderers if separated into modules; fallback to local functions
    try:
        from views.admin_tabs.analytics import render_analytics_tab as _ra
        from views.admin_tabs.user_management import render_user_management_tab as _rum
        from views.admin_tabs.matching import render_matching_tab as _rm
        from views.admin_tabs.clubs import render_clubs_tab as _rc
        from views.admin_tabs.verification import render_verification_tab as _rv
        from views.admin_tabs.data import render_data_tab as _rd
        with tabs[0]:
            _ra()
        with tabs[1]:
            _rum()
        with tabs[2]:
            _rm()
        with tabs[3]:
            _rc()
        with tabs[4]:
            _rv()
        with tabs[5]:
            _rd()
    except ImportError:
        # Fallback to legacy inline implementations below if modular imports fail
        with tabs[0]:
            render_analytics_tab()
        with tabs[1]:
            try:
                from views.admin_tabs.user_management import render_user_management_tab as _rum_fallback
                _rum_fallback()
            except ImportError:
                st.warning("사용자 관리 모듈을 찾을 수 없습니다.")
        with tabs[2]:
            render_matching_tab()
        with tabs[3]:
            render_clubs_tab()
        with tabs[4]:
            render_verification_tab()
        with tabs[5]:
            render_data_tab()


def render_analytics_tab():
    st.subheader("📈 분석 및 현황")
    users_all = persistence.load_list('users')
    clubs_all = persistence.load_list('clubs')
    runs_all = persistence.load_list('match_runs')
    reports_all = persistence.load_list('activity_reports')

    active_clubs = sum(1 for c in clubs_all if c.get('status') == 'Active')
    pending_reports = sum(
        1 for r in reports_all if r.get('status') == 'Pending')
    verified_reports = sum(
        1 for r in reports_all if r.get('status') == 'Verified')
    club_points = _club_points_map()
    total_points = sum(club_points.values())

    # Quick Actions / Summary strip
    with st.container(border=True):
        cqa1, cqa2, cqa3, cqa4, cqa5 = st.columns(5)
        # Show 0 when only demo_user exists (align with modular analytics tab logic)
        effective_user_count = 0 if (len(users_all) == 1 and users_all[0].get(
            'id') == 'demo_user') else len(users_all)
        cqa1.metric("사용자", effective_user_count)
        cqa2.metric("클럽", f"{len(clubs_all)} / 활성 {active_clubs}")
        cqa3.metric("보고서 대기", pending_reports)
        cqa4.metric("보고서 검증", verified_reports)
        cqa5.metric("총 포인트", total_points)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("직급 다양성 평균", _avg_metric(lambda c: {
              m['rank'] for m in users_all if m['id'] in c['member_ids']}, clubs_all))
    c2.metric("관심사 다양성 평균", _avg_metric(lambda c: {
              i for m in users_all if m['id'] in c['member_ids'] for i in m['interests']}, clubs_all))
    c3.metric("매칭 Run 수", len(runs_all))
    c4.metric("보고서 (대/검)", f"{pending_reports}/{verified_reports}")

    # (클럽 포인트 순위 Top 5 섹션 제거됨 - 데모 집중을 위해 간소화)

    # Verification metrics overview (aggregate pass rate simulation)
    if reports_all:
        verified_with_metrics = [
            r for r in reports_all if r.get('verification_metrics')]
        if verified_with_metrics:
            part_scores = [r['verification_metrics']['participants']
                           for r in verified_with_metrics]
            interest_scores = [r['verification_metrics']['interest']
                               for r in verified_with_metrics]
            diversity_scores = [r['verification_metrics']
                                ['diversity'] for r in verified_with_metrics]
            st.write("---")
            st.caption("최근 검증된 보고서의 평균 메트릭")
            m1, m2, m3 = st.columns(3)
            m1.metric("참여율", f"{sum(part_scores)/len(part_scores):.2f}")
            m2.metric(
                "관심사 정렬", f"{sum(interest_scores)/len(interest_scores):.2f}")
            m3.metric(
                "직급 다양성", f"{sum(diversity_scores)/len(diversity_scores):.2f}")


def _avg_metric(extractor, clubs_all):
    values = []
    for c in clubs_all:
        if c.get('member_ids'):
            extracted = extractor(c)
            if extracted:
                values.append(len(extracted))
    if not values:
        return "0"
    return f"{sum(values)/len(values):.2f}"


def render_matching_tab():
    st.subheader("⚙️ 매칭 실행")
    users_raw = persistence.load_list('users')
    if not users_raw:
        st.warning("매칭을 실행할 사용자가 없습니다. 먼저 사용자를 등록하거나 생성해주세요.")
        return
    effective_count = 0 if (len(users_raw) == 1 and users_raw[0].get(
        'id') == 'demo_user') else len(users_raw)
    st.info(f"현재 등록된 총 사용자: **{effective_count}명**")
    target_size = st.number_input(
        "클럽당 인원 (기본 6)", min_value=3, max_value=10, value=6)
    st.write("---")
    st.subheader("전체 재매칭")
    st.warning("주의: 이 작업은 기존 클럽에 영향을 주지 않고 새로운 클럽들을 추가 생성합니다.")
    if st.button("매칭 실행 / 새 버전 생성"):
        if len(users_raw) < target_size:
            st.error(f"매칭을 실행하려면 최소 {target_size}명의 사용자가 필요합니다.")
        else:
            user_objs = [User(**u) for u in users_raw]
            run_id = create_id_with_prefix('run')
            clubs = matching.compute_matches(
                user_objs, target_size=target_size, run_id=run_id)
            clubs_dicts = [asdict(c) for c in clubs]
            existing_clubs = persistence.load_list('clubs')
            existing_clubs.extend(clubs_dicts)
            persistence.replace_all('clubs', existing_clubs)
            runs = persistence.load_list('match_runs')
            run_meta = MatchRun(id=run_id, created_at=utc_now_iso(
            ), target_size=target_size, user_count=len(users_raw), club_count=len(clubs_dicts))
            runs.append(asdict(run_meta))
            persistence.replace_all('match_runs', runs)
            st.success(
                f"새 매칭 실행 완료. Run ID: {run_id}, 생성된 클럽 수: {len(clubs_dicts)}")
            st.balloons()


def render_clubs_tab():
    st.subheader("📊 클럽 관리")
    clubs_all = persistence.load_list('clubs')
    if not clubs_all:
        st.info("생성된 클럽이 없습니다.")
        return
    runs_meta = persistence.load_list('match_runs')
    # Chronological map for stable run numbering (oldest = #1)
    runs_chrono = sorted(runs_meta, key=lambda r: r.get('created_at', ''))
    run_number_map = {r['id']: i + 1 for i, r in enumerate(runs_chrono)}
    # Only runs that actually produced clubs
    runs_with_clubs = [r for r in runs_meta if any(
        c.get('match_run_id') == r['id'] for c in clubs_all)]
    if runs_with_clubs:
        # Display newest first by timestamp
        runs_display = sorted(runs_with_clubs, key=lambda r: r.get(
            'created_at', ''), reverse=True)
        label_map: dict[str, str] = {}
        for r in runs_display:
            # Keep seconds for uniqueness (avoid duplicate minute labels)
            created_disp = r['created_at'].replace('T', ' ')[:19]
            label = f"Run #{run_number_map.get(r['id'], '?')}: {created_disp} | size {r['target_size']} | clubs {r['club_count']}"
            label_map[label] = r['id']
        labels = list(label_map.keys())
        # Default select latest (index 0 after reverse sort)
        sel_label = st.selectbox("표시할 Match Run 선택", options=labels, index=0)
        selected_run_id = label_map[sel_label]
        clubs_to_display = [c for c in clubs_all if c.get(
            'match_run_id') == selected_run_id]
    else:
        st.warning("Run ID가 없는 클럽만 존재합니다. 전체를 표시합니다.")
        clubs_to_display = clubs_all
    points_map = _club_points_map()
    st.caption(f"표시된 클럽 수: {len(clubs_to_display)}")
    user_map = _user_map()
    modified = False
    for idx, c in enumerate(clubs_to_display, start=1):
        pts = points_map.get(c['id'], 0)
        display_name = c.get('name') or f"클럽 #{idx}"
        club_title = f"{display_name} | 인원 {len(c['member_ids'])} | 상태: {c.get('status', 'N/A')} | 포인트: {pts}"
        with st.expander(club_title):
            leader_name = _user_name(c['leader_id'], user_map)
            member_names = [_user_name(mid, user_map)
                            for mid in c['member_ids']]
            # Display-only cleanup: hide 'det_extra_' prefix.

            def _disp(n: str):
                return n[len('det_extra_'):] if isinstance(n, str) and n.startswith('det_extra_') else n
            leader_disp = _disp(leader_name)
            members_disp = [_disp(n) for n in member_names]
            st.write(f"**리더:** {leader_disp}")
            st.write(f"**멤버:** {', '.join(members_disp)}")
            if c.get('status') == 'Matched':
                leader_input = st.text_input(
                    "리더 이름 확인", key=f"leader_check_{c['id']}", help=f"'{leader_disp}'을(를) 입력하세요.")
                if leader_input.strip() == leader_disp:
                    chat_url = st.text_input(
                        "채팅 링크 (선택)", key=f"chat_{c['id']}")
                    if st.button(f"클럽 활성화", key=f"activate_{c['id']}"):
                        c['chat_link'] = chat_url if chat_url else ''
                        c['status'] = 'Active'
                        c['updated_at'] = utc_now_iso()
                        modified = True
    if modified:
        persistence.replace_all('clubs', clubs_all)
        st.success("클럽 상태 변경사항이 저장되었습니다.")
        st.rerun()


def render_verification_tab():
    st.subheader("✅ 활동 보고서 검증")
    reports = activity.list_reports()
    pending = [r for r in reports if r['status'] == 'Pending']
    if not pending:
        st.info("검증 대기 중인 보고서가 없습니다.")
    else:
        st.write(f"**{len(pending)}**개의 보고서가 검증을 기다리고 있습니다.")
        for r in pending:
            with st.expander(f"Report `{r['id']}` | Club `{r['club_id']}` | Date: {r['date']}"):
                st.text_area("내용", r['formatted_report'],
                             height=150, disabled=True)
                if st.button(f"AI 검증 실행", key=f"verify_{r['id']}"):
                    with st.spinner("AI 검증 시뮬레이션 중..."):
                        time.sleep(1)
                        activity.verify_report(r['id'])
                    st.success("검증 완료! 포인트가 지급되었습니다.")
                    st.rerun()
    st.divider()
    st.subheader("검증 완료된 보고서")
    verified = [r for r in reports if r['status'] == 'Verified']
    if verified:
        st.dataframe(verified, use_container_width=True)
    else:
        st.caption("검증 완료된 보고서가 없습니다.")


def render_data_tab():
    st.subheader("💾 데이터 관리")
    with st.container(border=True):
        st.subheader("샘플 사용자 생성")
        if st.button("샘플 사용자 15명 생성"):
            users = persistence.load_list('users')
            if users:
                st.info("이미 사용자가 존재하여, 기존 목록에 15명을 추가합니다.")
            from demo import sample_data
            new_users = [asdict(u) for u in sample_data.make_users(15)]
            users.extend(new_users)
            persistence.replace_all('users', users)
            st.success("샘플 사용자 추가 완료!")
            st.rerun()
    with st.container(border=True):
        st.subheader("데이터 내보내기 (CSV)")
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("사용자"):
            st.download_button("다운로드: users.csv", _to_csv(
                persistence.load_list('users')), "users.csv", "text/csv")
        if c2.button("클럽"):
            st.download_button("다운로드: clubs.csv", _to_csv(
                persistence.load_list('clubs')), "clubs.csv", "text/csv")
        if c3.button("보고서"):
            st.download_button("다운로드: reports.csv", _to_csv(
                persistence.load_list('activity_reports')), "reports.csv", "text/csv")
        if c4.button("매칭기록"):
            st.download_button("다운로드: runs.csv", _to_csv(
                persistence.load_list('match_runs')), "runs.csv", "text/csv")
    with st.expander("🚨 Danger Zone: 데이터 초기화"):
        st.warning("주의: 이 작업은 모든 사용자, 클럽, 보고서, 매칭 기록을 영구적으로 삭제합니다. 되돌릴 수 없습니다.")
        confirm = st.checkbox("위험을 인지했으며, 모든 데이터를 삭제하는 데 동의합니다.")
        if confirm:
            code_input = st.text_input("삭제를 원하시면 'ERASE ALL DATA'를 입력하세요.")
            if code_input == "ERASE ALL DATA":
                if st.button("모든 데이터 영구 삭제", type="primary"):
                    for key in ['users', 'clubs', 'activity_reports', 'match_runs']:
                        persistence.replace_all(key, [])
                    st.success("모든 애플리케이션 데이터가 삭제되었습니다.")
                    time.sleep(2)
                    st.rerun()


def _to_csv(data: list[dict]):
    if not data:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue()
