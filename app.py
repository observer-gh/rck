from typing import Optional, List, Dict, Any, Iterable
import streamlit as st
from services import persistence
from domain.models import User, MatchRun
from utils.ids import create_id_with_prefix
from services.matching import compute_matches
from services.sample_data import make_users
from services import activity
from dataclasses import asdict
import datetime as dt
import time


# ---------------- Constants ---------------- #
REGION_OPTIONS = ["서울", "부산", "대전", "대구"]
RANK_OPTIONS = ["사원", "주임", "대리", "과장"]
INTEREST_OPTIONS = ["축구", "영화보기", "보드게임", "러닝", "독서", "헬스", "요리", "사진", "등산"]
ATMOS_OPTIONS = ["외향", "내향", "밸런스"]

# ---------------- Utility ---------------- #


def utc_now_iso() -> str:
    """Return current UTC time in ISO format with 'Z' suffix."""
    return dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z')


def is_duplicate_user(name: str, region: str, users: List[Dict[str, Any]], exclude_id: Optional[str] = None) -> bool:
    """Check if a (name, region) combo already exists (case-insensitive).

    exclude_id: ignore this user id (when editing)
    """
    name_norm = name.strip().lower()
    region_norm = region.strip().lower()
    for u in users:
        if exclude_id and u['id'] == exclude_id:
            continue
        if u['name'].strip().lower() == name_norm and u['region'].strip().lower() == region_norm:
            return True
    return False


st.set_page_config(page_title="AI Club Matching Demo", layout="wide")


def load_users():
    return persistence.load_list('users')


def save_users(users):
    persistence.replace_all('users', users)


def load_clubs():
    return persistence.load_list('clubs')


def save_clubs(clubs):
    persistence.replace_all('clubs', clubs)


# Helper lookups
def _user_map():
    return {u['id']: u for u in load_users()}


def _user_name(uid: str, user_map: Dict[str, Dict[str, Any]]):
    u = user_map.get(uid)
    return u['name'] if u else uid


def _club_points_map() -> Dict[str, int]:
    reports = persistence.load_list('activity_reports')
    pts: Dict[str, int] = {}
    for r in reports:
        if r.get('status') == 'Verified':
            pts[r['club_id']] = pts.get(
                r['club_id'], 0) + int(r.get('points_awarded', 0))
    return pts


def _clear_all_data():
    """Wipe all persisted lists (irreversible)."""
    for key in ['users', 'clubs', 'activity_reports', 'match_runs']:
        persistence.replace_all(key, [])


st.sidebar.title("Navigation")
show_ids = st.sidebar.checkbox("Show internal IDs", value=False)
# Health panel
with st.sidebar.expander("Health / Metrics", expanded=False):
    users_all = persistence.load_list('users')
    clubs_all_tmp = persistence.load_list('clubs')
    runs_all = persistence.load_list('match_runs')
    reports_all = persistence.load_list('activity_reports')
    active_clubs = sum(1 for c in clubs_all_tmp if c.get('status') == 'Active')
    pending_reports = sum(
        1 for r in reports_all if r.get('status') == 'Pending')
    verified_reports = sum(
        1 for r in reports_all if r.get('status') == 'Verified')
    # Aggregate verified points per club
    club_points: Dict[str, int] = {}
    for r in reports_all:
        if r.get('status') == 'Verified':
            club_points[r['club_id']] = club_points.get(
                r['club_id'], 0) + int(r.get('points_awarded', 0))
    total_points = sum(club_points.values())
    st.metric("Users", len(users_all))
    st.metric("Clubs", len(clubs_all_tmp))
    st.metric("Active Clubs", active_clubs)
    st.metric("Runs", len(runs_all))
    st.metric("Reports P/V", f"{pending_reports}/{verified_reports}")
    st.metric("총 포인트(검증)", total_points)
    if club_points:
        # Show small table of top clubs by points (friendly label: leader name if available)
        user_map_local = _user_map()
        clubs_all_full = {c['id']: c for c in clubs_all_tmp}
        top = sorted(club_points.items(), key=lambda x: x[1], reverse=True)[:5]
        st.caption("클럽 포인트 Top5")
        for cid, pts in top:
            leader_id = clubs_all_full.get(cid, {}).get('leader_id')
            leader_name = _user_name(
                leader_id, user_map_local) if leader_id else '?'
            st.write(f"{leader_name} 팀: {pts}")
page = st.sidebar.radio(
    "Go to",
    [
        "User Signup",
        "Matching (Admin)",
        "Results",
        "Activity Reports",
        "Verification (Admin)",
        "Match Runs",
        "Seed Sample Users",
    ],
    index=0,
)

# --- Demo Guide (non-developer quick start) --- #


def _demo_seed_users(n: int = 15):
    users = load_users()
    if users:
        st.info("이미 사용자가 있어 시드하지 않았습니다.")
        return
    new = [asdict(u) for u in make_users(n)]
    save_users(new)
    st.success(f"샘플 사용자 {n}명 생성 완료")


def _demo_quick_match(target_size: int = 5):
    users_raw = load_users()
    if not users_raw:
        st.warning("먼저 Seed Users 실행")
        return
    from domain.models import MatchRun as _MR
    user_objs = [User(**u) for u in users_raw]
    run_id = create_id_with_prefix('run')
    clubs = compute_matches(user_objs, target_size=target_size, run_id=run_id)
    clubs_dicts = [asdict(c) for c in clubs]
    existing = load_clubs()
    existing.extend(clubs_dicts)
    save_clubs(existing)
    runs = persistence.load_list('match_runs')
    run_meta = _MR(id=run_id, created_at=utc_now_iso(
    ), target_size=target_size, user_count=len(users_raw), club_count=len(clubs_dicts))
    runs.append(asdict(run_meta))
    persistence.replace_all('match_runs', runs)
    st.success(f"Quick Match 완료 (Run {run_id}, 클럽 {len(clubs_dicts)})")


with st.sidebar.expander("Demo Guide", expanded=True):
    st.markdown(
        """**60초 체험 가이드**\n\n1. 'Seed Users' 로 샘플 생성\n2. 'Quick Match' 실행\n3. Matching (Admin) → 클럽 확인 및 활성화\n4. Activity Reports → 보고서 제출\n5. Verification → 검증 후 포인트 확인"""
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Seed Users", key="demo_seed_btn"):
            _demo_seed_users()
    with c2:
        if st.button("Quick Match", key="demo_quick_btn"):
            _demo_quick_match()


if page == "User Signup":
    st.header("사용자 등록")
    name = st.text_input("이름")
    region = st.selectbox("지역", REGION_OPTIONS)
    rank = st.selectbox("직급", RANK_OPTIONS)
    interests = st.multiselect("관심사", INTEREST_OPTIONS)
    atmosphere = st.selectbox("선호 분위기", ATMOS_OPTIONS)
    if st.button("저장", disabled=not (name and interests)):
        users = load_users()
        if is_duplicate_user(name, region, users):
            st.error("중복 사용자 (이름+지역) 존재. 저장 취소.")
        else:
            uid = create_id_with_prefix('u')
            user = User(id=uid, name=name, region=region, rank=rank,
                        interests=interests, preferred_atmosphere=atmosphere)
            users.append(asdict(user))
            save_users(users)
            st.success(f"저장 완료: {name}")
    st.divider()
    st.subheader("현재 사용자 (편집/삭제)")
    users = load_users()
    if users:
        display_map = {f"{u['name']} ({u['region']})": u['id'] for u in users}
        sel_disp = st.selectbox(
            "사용자 선택", options=["-"] + list(display_map.keys()))
        if sel_disp != "-":
            sel_id = display_map[sel_disp]
            u = next((x for x in users if x['id'] == sel_id), None)
            if u:
                with st.expander(f"편집: {u['name']} ({u['region']})", expanded=True):
                    new_name = st.text_input(
                        "이름", value=u['name'], key=f"edit_name_{sel_id}")
                    new_region = st.selectbox("지역", REGION_OPTIONS, index=REGION_OPTIONS.index(
                        u['region']), key=f"edit_region_{sel_id}")
                    new_rank = st.selectbox("직급", RANK_OPTIONS, index=RANK_OPTIONS.index(
                        u['rank']), key=f"edit_rank_{sel_id}")
                    new_interests = st.multiselect(
                        "관심사", INTEREST_OPTIONS, default=u['interests'], key=f"edit_interests_{sel_id}")
                    new_atmos = st.selectbox("선호 분위기", ATMOS_OPTIONS, index=ATMOS_OPTIONS.index(
                        u['preferred_atmosphere']), key=f"edit_atmos_{sel_id}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("저장 변경", key=f"save_user_{sel_id}"):
                            if is_duplicate_user(new_name, new_region, users, exclude_id=sel_id):
                                st.error("중복 사용자 (이름+지역) 존재. 변경 취소.")
                            else:
                                u.update({
                                    'name': new_name,
                                    'region': new_region,
                                    'rank': new_rank,
                                    'interests': new_interests,
                                    'preferred_atmosphere': new_atmos
                                })
                                save_users(users)
                                st.success("업데이트 완료")
                                st.rerun()
                    with col2:
                        if st.button("삭제", key=f"del_user_{sel_id}"):
                            users = [x for x in users if x['id'] != sel_id]
                            save_users(users)
                            st.warning("삭제됨 (매칭 재실행 필요)")
                            st.rerun()
        # Friendlier table (hide internal id via index) -- but keep id column for transparency
        st.dataframe(users, use_container_width=True)
    else:
        st.info("아직 등록된 사용자가 없습니다.")


elif page == "Matching (Admin)":
    def run_matching(users_raw, target_size: int):
        """Execute a matching run and persist clubs + run metadata."""
        user_objs = [User(**u) for u in users_raw]
        run_id = create_id_with_prefix('run')
        clubs = compute_matches(
            user_objs, target_size=target_size, run_id=run_id)
        clubs_dicts = [asdict(c) for c in clubs]
        existing = load_clubs()
        existing.extend(clubs_dicts)
        save_clubs(existing)
        runs = persistence.load_list('match_runs')
        run_meta = MatchRun(
            id=run_id,
            created_at=utc_now_iso(),
            target_size=target_size,
            user_count=len(users_raw),
            club_count=len(clubs_dicts)
        )
        runs.append(asdict(run_meta))
        persistence.replace_all('match_runs', runs)
        return run_id, len(clubs_dicts)

    st.header("매칭 실행 (Admin)")
    users_raw = load_users()
    if not users_raw:
        st.warning("사용자가 없습니다.")
    else:
        st.caption(f"총 사용자: {len(users_raw)}")
        target_size = st.number_input(
            "그룹 인원 (기본 5)", min_value=3, max_value=10, value=5)
        col_new, col_rerun = st.columns(2)
        with col_new:
            if st.button("매칭 실행 / 새 버전"):
                run_id, club_count = run_matching(users_raw, target_size)
                st.success(f"새 매칭 실행 완료. Run: {run_id} | 클럽 {club_count}")
        with col_rerun:
            runs = persistence.load_list('match_runs')
            if runs:
                runs_sorted = sorted(runs, key=lambda r: r['created_at'])
                last = runs_sorted[-1]
                if st.button("마지막 설정 재실행"):
                    run_id, club_count = run_matching(
                        users_raw, last['target_size'])
                    st.success(f"재실행 완료. Run: {run_id} | 클럽 {club_count}")
            else:
                st.caption("이전 실행 없음")

    st.subheader("클럽 결과 (Run 별 필터)")
    clubs_all = load_clubs()
    if clubs_all:
        # Build friendly run labels
        runs_meta = persistence.load_list('match_runs')
        run_order = {r['id']: i+1 for i,
                     r in enumerate(sorted(runs_meta, key=lambda r: r['created_at']))}
        run_ids = sorted({c.get('match_run_id', '')
                         for c in clubs_all if c.get('match_run_id')}, reverse=True)
        if run_ids:
            label_map: Dict[str, str] = {}
            for rid in run_ids:
                meta = next((r for r in runs_meta if r['id'] == rid), None)
                if meta:
                    created = meta['created_at'].replace('T', ' ')[:16]
                    label_map[f"Run #{run_order.get(rid, '?')}: {created} | size {meta['target_size']} | clubs {meta['club_count']}"] = rid
                else:
                    label_map[rid] = rid
            sel_label = st.selectbox(
                "Match Run 선택", options=list(label_map.keys()))
            selected_run = label_map[sel_label]
            clubs = [c for c in clubs_all if c.get(
                'match_run_id') == selected_run]
        else:
            st.warning("Run ID 없는 클럽만 존재. 전체 표시")
            clubs = clubs_all
        # Points map for display
        points_map = _club_points_map()
        st.caption(
            f"클럽 수: {len(clubs)} (검증 포인트 합계: {sum(points_map.get(c['id'], 0) for c in clubs)})")
        import csv
        import io
        if st.button("클럽 CSV 다운로드"):
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(
                ["club_id", "member_ids", "leader_id", "status", "run_id"])
            for c in clubs:
                writer.writerow([c['id'], '|'.join(c['member_ids']), c['leader_id'], c.get(
                    'status', ''), c.get('match_run_id', '')])
            st.download_button("다운로드", output.getvalue(),
                               file_name="clubs.csv", mime="text/csv")
        modified = False
        user_map = _user_map()
        club_pts_map = _club_points_map()
        for idx, c in enumerate(clubs, start=1):
            pts = club_pts_map.get(c['id'], 0)
            club_title = f"클럽 #{idx} | 인원 {len(c['member_ids'])} | 상태 {c.get('status', '?')} | 포인트 {pts}"
            with st.expander(club_title):
                leader_name = _user_name(c['leader_id'], user_map)
                member_names = [_user_name(mid, user_map)
                                for mid in c['member_ids']]
                st.write("리더:", f"{leader_name}" +
                         (f" ({c['leader_id']})" if show_ids else ''))
                st.write("멤버:", ', '.join(
                    m + (f" ({mid})" if show_ids else '') for m, mid in zip(member_names, c['member_ids'])))
                with st.expander("점수 상세"):
                    st.json(c['match_score_breakdown'])
                exp = c.get('explanations') or {}
                if exp:
                    with st.expander("매칭 설명"):
                        for uid, peers in exp.items():
                            uname = _user_name(uid, user_map)
                            rendered = '; '.join(
                                f"{_user_name(pid, user_map)}:{reason}" for pid, reason in peers.items())
                            st.write(f"{uname} → {rendered}")
                if c.get('status') == 'Matched':
                    leader_input = st.text_input(
                        f"리더 이름 입력 (확인)", key=f"leader_check_{c['id']}")
                    if leader_input and leader_input.strip() == leader_name:
                        chat_url = st.text_input(
                            f"채팅 링크 (선택)", key=f"chat_{c['id']}")
                        if st.button(f"활성화 (#{idx})", key=f"activate_{c['id']}"):
                            if chat_url:
                                c['chat_link'] = chat_url
                            c['status'] = 'Active'
                            c['updated_at'] = utc_now_iso()
                            modified = True
        if modified:
            save_clubs(clubs_all)
            st.success("업데이트 저장됨")
    else:
        st.info("아직 생성된 클럽이 없습니다.")

elif page == "Results":
    st.header("현재 클럽 결과")
    clubs_all = load_clubs()
    if not clubs_all:
        st.info("아직 생성된 클럽이 없습니다.")
    else:
        # Preload user map and points
        user_map = _user_map()
        pts_map = _club_points_map()
        for idx, c in enumerate(clubs_all, start=1):
            with st.expander(f"클럽 #{idx} | 인원 {len(c['member_ids'])} | 상태 {c.get('status', '?')} | 포인트 {pts_map.get(c['id'], 0)}"):
                leader_name = _user_name(c['leader_id'], user_map)
                member_names = [_user_name(mid, user_map)
                                for mid in c['member_ids']]
                st.write("리더:", f"{leader_name}" +
                         (f" ({c['leader_id']})" if show_ids else ''))
                st.write("멤버:", ', '.join(
                    m + (f" ({mid})" if show_ids else '') for m, mid in zip(member_names, c['member_ids'])))
                with st.expander("점수 상세"):
                    st.json(c['match_score_breakdown'])
                exp = c.get('explanations') or {}
                if exp:
                    with st.expander("매칭 설명"):
                        for uid, peers in exp.items():
                            uname = _user_name(uid, user_map)
                            rendered = '; '.join(
                                f"{_user_name(pid, user_map)}:{reason}" for pid, reason in peers.items())
                            st.write(f"{uname} → {rendered}")

elif page == "Activity Reports":
    st.header("활동 보고서 제출")
    clubs_all = load_clubs()
    if not clubs_all:
        st.info("클럽이 없습니다.")
    else:
        club_options = [f"{c['id']} ({c.get('status')})" for c in clubs_all if c.get(
            'status') == 'Active']
        if not club_options:
            st.warning("활성화된 (Active) 클럽이 없습니다.")
        else:
            choice = st.selectbox("클럽 선택", options=club_options)
            club_id = choice.split()[0]
            date = st.date_input("활동 날짜")
            raw_text = st.text_area("활동 내용")
            photo = st.file_uploader("사진 업로드 (시뮬레이션)")
            part_count = st.number_input(
                "참여 인원(선택)", min_value=0, max_value=100, value=0)
            if st.button("보고서 제출", disabled=not raw_text):
                photo_name = photo.name if photo is not None else 'no_photo'
                rep = activity.create_activity_report(
                    club_id=club_id,
                    date=str(date),
                    photo_name=photo_name,
                    raw_text=raw_text,
                    participant_override=part_count if part_count > 0 else None,
                )
                st.success(f"보고서 생성: {rep.id}")
    st.divider()
    st.subheader("제출된 보고서")
    reports = activity.list_reports()
    if reports:
        st.dataframe(reports, use_container_width=True)
        # Export CSV
        import csv
        import io
        if st.button("보고서 CSV 다운로드"):
            out = io.StringIO()
            w = csv.writer(out)
            w.writerow(["id", "club_id", "date",
                       "status", "points", "verified_at"])
            for r in reports:
                w.writerow([r['id'], r['club_id'], r['date'], r.get(
                    'status', ''), r.get('points_awarded', 0), r.get('verified_at', '')])
            st.download_button("다운로드 Reports", out.getvalue(
            ), file_name="activity_reports.csv", mime="text/csv")
    else:
        st.caption("아직 없음")

elif page == "Verification (Admin)":
    st.header("보고서 검증 (시뮬레이션)")
    reports = activity.list_reports()
    pending = [r for r in reports if r['status'] == 'Pending']
    if not pending:
        st.info("대기중 보고서 없음")
    else:
        for r in pending:
            with st.expander(f"Report {r['id']} | Club {r['club_id']}"):
                st.write(r['formatted_report'])
                if st.button(f"AI 검증 실행 ({r['id']})"):
                    with st.spinner("AI 검증 중..."):
                        time.sleep(2)
                    activity.verify_report(r['id'])
                    st.success("검증 완료")
                    st.rerun()
    st.divider()
    st.subheader("전체 보고서")
    all_reports = activity.list_reports()
    if all_reports:
        st.dataframe(all_reports, use_container_width=True)
    else:
        st.caption("없음")

elif page == "Match Runs":
    st.header("매칭 실행 기록")
    runs = persistence.load_list('match_runs')
    if not runs:
        st.info("실행 기록 없음")
    else:
        runs_sorted = sorted(runs, key=lambda r: r['created_at'], reverse=True)
        st.dataframe(runs_sorted, use_container_width=True)
        # Export runs
        import csv
        import io
        if st.button("Run CSV"):
            out = io.StringIO()
            w = csv.writer(out)
            w.writerow(["run_id", "created_at", "target_size",
                       "user_count", "club_count", "superseded"])
            for r in runs_sorted:
                w.writerow([r['id'], r['created_at'], r['target_size'],
                           r['user_count'], r['club_count'], r.get('superseded', False)])
            st.download_button("다운로드 Run CSV", out.getvalue(
            ), file_name="match_runs.csv", mime="text/csv")
        run_ids = [r['id'] for r in runs_sorted]
        sel = st.selectbox("Supersede Run 선택", options=[''] + run_ids)
        if sel and st.button("Supersede 표시"):
            for r in runs:
                if r['id'] == sel:
                    r['superseded'] = True
            persistence.replace_all('match_runs', runs)
            st.success("표시 완료")
            st.rerun()

elif page == "Seed Sample Users":
    st.header("샘플 사용자 생성")
    if st.button("15명 생성"):
        users = load_users()
        if users:
            st.warning("이미 사용자 존재. 추가만 진행.")
        new = [asdict(u) for u in make_users(15)]
        users.extend(new)
        save_users(users)
        st.success("샘플 추가 완료")
    users_now = load_users()
    st.dataframe(users_now, use_container_width=True)
    import csv
    import io
    col1, col2 = st.columns(2)
    with col1:
        if st.button("사용자 CSV 다운로드"):
            out = io.StringIO()
            w = csv.writer(out)
            w.writerow(["id", "name", "region", "rank", "interests",
                       "preferred_atmosphere", "created_at"])
            for u in users_now:
                w.writerow([u['id'], u['name'], u['region'], u['rank'], '|'.join(u.get(
                    'interests', [])), u.get('preferred_atmosphere', ''), u.get('created_at', '')])
            st.download_button("다운로드 Users", out.getvalue(),
                               file_name="users.csv", mime="text/csv")
    with col2:
        up = st.file_uploader("사용자 CSV 업로드")
        if up is not None and st.button("CSV 병합"):
            content = up.getvalue().decode('utf-8').splitlines()
            reader = csv.DictReader(content)
            existing = {(u['name'].strip().lower(),
                         u['region'].strip().lower()): u for u in users_now}
            added = 0
            for row in reader:
                key = (row['name'].strip().lower(),
                       row['region'].strip().lower())
                if key in existing:
                    continue
                interests = row.get('interests', '')
                interests_list = [x for x in interests.split('|') if x]
                users_now.append({
                    'id': row.get('id') or create_id_with_prefix('u'),
                    'name': row['name'],
                    'region': row['region'],
                    'rank': row.get('rank', ''),
                    'interests': interests_list,
                    'preferred_atmosphere': row.get('preferred_atmosphere', ''),
                    'created_at': row.get('created_at') or utc_now_iso()
                })
                added += 1
            save_users(users_now)
            st.success(f"CSV 병합 완료. 추가 {added}명")
            st.rerun()

st.sidebar.markdown("---")
with st.sidebar.expander("Danger Zone", expanded=False):
    st.warning("모든 데이터 (사용자, 클럽, 보고서, 실행기록) 삭제합니다. 되돌릴 수 없습니다.")
    ack = st.checkbox("이 작업의 위험을 이해했습니다", key="ack_erase")
    code = st.text_input("확인 코드 입력: ERASE", key="erase_code") if ack else ""
    if ack and code == "ERASE":
        if st.button("Erase All Data", type="primary"):
            _clear_all_data()
            st.success("모든 데이터 삭제 완료")
            st.rerun()
st.sidebar.caption(
    f"Data dir: data | {dt.datetime.now(dt.timezone.utc).strftime('%H:%M:%S')}Z")
