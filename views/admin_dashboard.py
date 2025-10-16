import streamlit as st
from dataclasses import asdict
from services import persistence, activity, matching, sample_data
from services import users as user_svc
from domain.models import User, MatchRun
from utils.ids import create_id_with_prefix
import datetime as dt
import time
import csv
import io
from services.survey import QUESTIONS, classify_personality
from ui.components import user_badge


def _user_map():
    return {u['id']: u for u in persistence.load_list('users')}


def _user_name(uid, user_map):
    u = user_map.get(uid)
    return u['name'] if u else uid


def _club_points_map():
    reports = persistence.load_list('activity_reports')
    pts = {}
    for r in reports:
        if r.get('status') == 'Verified':
            pts[r['club_id']] = pts.get(
                r['club_id'], 0) + int(r.get('points_awarded', 0))
    return pts


def utc_now_iso():
    return dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z')


def view():
    st.header("어드민 대시보드")
    st.markdown("이곳에서 데이터 관리, 매칭 실행, 활동 보고서 검증 등 주요 관리 작업을 수행합니다.")

    tabs = st.tabs([
        "📈 분석 및 현황",
        "👤 사용자 관리",
        "⚙️ 매칭 실행",
        "📊 클럽 관리",
        "✅ 보고서 검증",
        "💾 데이터 관리",
    ])

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


def render_user_management_tab():
    st.subheader("👤 사용자 관리")
    users = persistence.load_list('users')
    if not users:
        st.info("등록된 사용자가 없습니다.")
        return
    users.sort(key=lambda u: u['name'])
    display_map = {f"{u['name']} ({u['region']})": u['id'] for u in users}
    sel_disp = st.selectbox("사용자 선택", options=["-"] + list(display_map.keys()))
    if sel_disp != "-":
        sel_id = display_map[sel_disp]
        st.session_state.current_user_id = sel_id
        u = next((x for x in users if x['id'] == sel_id), None)
        if u:
            with st.expander(f"편집: {u['name']} ({u['region']})", expanded=True):
                new_name = st.text_input(
                    "이름", value=u['name'], key=f"adm_edit_name_{sel_id}")
                new_employee_number = st.text_input("사번", value=u.get(
                    'employee_number', ''), key=f"adm_edit_emp_{sel_id}")
                REGION_OPTIONS = ["서울", "부산", "대전", "대구"]
                RANK_OPTIONS = ["사원", "대리", "과장", "차장", "부장"]
                INTEREST_OPTIONS = ["축구", "영화보기", "보드게임",
                                    "러닝", "독서", "헬스", "요리", "사진", "등산"]
                new_region = st.selectbox("지역", REGION_OPTIONS, index=REGION_OPTIONS.index(
                    u['region']), key=f"adm_edit_region_{sel_id}")
                new_rank = st.selectbox("직급", RANK_OPTIONS, index=RANK_OPTIONS.index(
                    u['rank']), key=f"adm_edit_rank_{sel_id}")
                new_interests = st.multiselect(
                    "관심사", INTEREST_OPTIONS, default=u['interests'], key=f"adm_edit_interests_{sel_id}")
                existing_answers = u.get('survey_answers') or [
                    3] * len(QUESTIONS)
                new_answers = []
                for i, q in enumerate(QUESTIONS):
                    new_answers.append(
                        st.slider(q, 1, 5, existing_answers[i], key=f"adm_edit_q_{sel_id}_{i}"))
                col1, col2, col3 = st.columns(3)
                if col1.button("저장", key=f"adm_save_{sel_id}"):
                    safe_name = new_name or ""
                    safe_region = new_region or ""
                    if user_svc.is_duplicate_user(safe_name, safe_region, users, exclude_id=sel_id):
                        st.error("중복 사용자 (이름+지역) 존재. 변경 취소.")
                    else:
                        u.update({
                            'name': safe_name,
                            'employee_number': new_employee_number,
                            'region': safe_region,
                            'rank': new_rank,
                            'interests': new_interests,
                            'personality_trait': classify_personality(new_answers),
                            'survey_answers': new_answers
                        })
                        persistence.replace_all('users', users)
                        st.success("업데이트 완료")
                        st.rerun()
                if col2.button("삭제", key=f"adm_del_{sel_id}"):
                    users = [x for x in users if x['id'] != sel_id]
                    persistence.replace_all('users', users)
                    st.warning("삭제됨 (매칭 재실행 필요)")
                    st.rerun()
                if col3.button("현재 사용자로 설정", key=f"adm_setcur_{sel_id}"):
                    st.session_state.current_user_id = sel_id
                    st.success("현재 사용자 세션이 업데이트되었습니다.")
    st.markdown("---")
    st.subheader("사용자 목록")
    for u in users:
        user_badge(u)


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

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 사용자", len(users_all))
    c2.metric("총 클럽", len(clubs_all))
    c3.metric("활성 클럽", active_clubs)
    c4.metric("매칭 실행 횟수", len(runs_all))
    c1.metric("보고서 (대기/검증)", f"{pending_reports}/{verified_reports}")
    c2.metric("총 포인트 (검증)", total_points)

    if clubs_all:
        rank_diversities = [len({m['rank'] for m in users_all if m['id'] in c['member_ids']})
                            for c in clubs_all if c['member_ids']]
        interest_varieties = [len({i for m in users_all if m['id'] in c['member_ids']
                                  for i in m['interests']}) for c in clubs_all if c['member_ids']]

        avg_rank_diversity = sum(rank_diversities) / \
            len(rank_diversities) if rank_diversities else 0
        avg_interest_variety = sum(
            interest_varieties) / len(interest_varieties) if interest_varieties else 0

        c3.metric("평균 직급 다양성", f"{avg_rank_diversity:.2f}")
        c4.metric("평균 관심사 다양성", f"{avg_interest_variety:.2f}")

    st.write("---")
    st.subheader("클럽 포인트 순위 Top 5")
    if club_points:
        user_map = _user_map()
        clubs_map = {c['id']: c for c in clubs_all}
        top_clubs = sorted(club_points.items(),
                           key=lambda item: item[1], reverse=True)[:5]
        leader_names = []
        points = []
        for cid, pts in top_clubs:
            club = clubs_map.get(cid)
            leader_name = _user_name(
                club['leader_id'], user_map) if club else '?'
            leader_names.append(f"{leader_name} 팀")
            points.append(pts)
        st.bar_chart({"클럽": points, "이름": leader_names}, x="이름", y="클럽")
    else:
        st.caption("검증된 포인트가 있는 클럽이 없습니다.")


def render_matching_tab():
    st.subheader("⚙️ 매칭 실행")
    users_raw = persistence.load_list('users')
    if not users_raw:
        st.warning("매칭을 실행할 사용자가 없습니다. 먼저 사용자를 등록하거나 생성해주세요.")
        return
    st.info(f"현재 등록된 총 사용자: **{len(users_raw)}명**")
    # Auto-seed pathway when only demo user exists
    if len(users_raw) == 1 and users_raw[0].get('id') == 'demo_user':
        st.warning(
            "현재 데모 사용자 1명만 존재합니다. 아래 버튼으로 동료 9명을 자동 생성하고 즉시 매칭을 실행할 수 있습니다.")
        if st.button("동료 9명 자동생성 + 매칭 실행", type="primary"):
            from services import sample_data
            # generate 9 additional users
            new_users = [asdict(u) for u in sample_data.make_users(9)]
            users_all = users_raw + new_users
            persistence.replace_all('users', users_all)
            # run matching with default target size 5
            user_objs = [User(**u) for u in users_all]
            run_id = create_id_with_prefix('run')
            clubs = matching.compute_matches(
                user_objs, target_size=5, run_id=run_id)
            clubs_dicts = [asdict(c) for c in clubs]
            existing_clubs = persistence.load_list('clubs')
            existing_clubs.extend(clubs_dicts)
            persistence.replace_all('clubs', existing_clubs)
            runs = persistence.load_list('match_runs')
            run_meta = MatchRun(id=run_id, created_at=utc_now_iso(
            ), target_size=5, user_count=len(users_all), club_count=len(clubs_dicts))
            runs.append(asdict(run_meta))
            persistence.replace_all('match_runs', runs)
            st.success(
                f"자동 생성 및 매칭 완료. Run ID: {run_id}, 생성된 클럽 수: {len(clubs_dicts)}")
            st.balloons()
            st.rerun()
    target_size = st.number_input(
        "클럽당 인원 (기본 5)", min_value=3, max_value=10, value=5)
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
    run_order = {r['id']: i + 1 for i,
                 r in enumerate(sorted(runs_meta, key=lambda r: r['created_at']))}
    run_ids = sorted({c.get('match_run_id', '')
                     for c in clubs_all if c.get('match_run_id')}, reverse=True)
    selected_run_id = None
    if run_ids:
        label_map = {}
        for rid in run_ids:
            meta = next((r for r in runs_meta if r['id'] == rid), None)
            if meta:
                created = meta['created_at'].replace('T', ' ')[:16]
                label_map[f"Run #{run_order.get(rid, '?')}: {created} | size {meta['target_size']} | clubs {meta['club_count']}"] = rid
            else:
                label_map[rid] = rid
        sel_label = st.selectbox(
            "표시할 Match Run 선택", options=list(label_map.keys()))
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
        club_title = f"클럽 #{idx} | 인원 {len(c['member_ids'])} | 상태: {c.get('status', 'N/A')} | 포인트: {pts}"
        with st.expander(club_title):
            leader_name = _user_name(c['leader_id'], user_map)
            member_names = [_user_name(mid, user_map)
                            for mid in c['member_ids']]
            st.write(f"**리더:** {leader_name}")
            st.write(f"**멤버:** {', '.join(member_names)}")
            if c.get('status') == 'Matched':
                leader_input = st.text_input(
                    "리더 이름 확인", key=f"leader_check_{c['id']}", help=f"'{leader_name}'을(를) 입력하세요.")
                if leader_input.strip() == leader_name:
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
            from services import sample_data
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
                    for key in ['clubs', 'activity_reports', 'match_runs']:
                        persistence.replace_all(key, [])
                    # Reset users but re-add demo user via service helper
                    persistence.replace_all('users', [])
                    user_svc.load_users()  # triggers ensure_demo_user persistence
                    st.success("모든 애플리케이션 데이터가 삭제되었습니다 (데모사용자 제외).")
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
