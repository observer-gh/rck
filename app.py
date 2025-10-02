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


st.sidebar.title("Navigation")
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
    st.metric("Users", len(users_all))
    st.metric("Clubs", len(clubs_all_tmp))
    st.metric("Active Clubs", active_clubs)
    st.metric("Runs", len(runs_all))
    st.metric("Reports P/V", f"{pending_reports}/{verified_reports}")
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
        # Editable selection
        user_ids = [u['id'] for u in users]
        sel = st.selectbox("사용자 선택", options=["-"] + user_ids)
        if sel != "-":
            # Find user
            u = next((x for x in users if x['id'] == sel), None)
            if u:
                with st.expander(f"편집 {sel}", expanded=True):
                    new_name = st.text_input(
                        "이름", value=u['name'], key=f"edit_name_{sel}")
                    new_region = st.selectbox("지역", REGION_OPTIONS, index=REGION_OPTIONS.index(
                        u['region']), key=f"edit_region_{sel}")
                    new_rank = st.selectbox("직급", RANK_OPTIONS, index=RANK_OPTIONS.index(
                        u['rank']), key=f"edit_rank_{sel}")
                    new_interests = st.multiselect(
                        "관심사", INTEREST_OPTIONS, default=u['interests'], key=f"edit_interests_{sel}")
                    new_atmos = st.selectbox("선호 분위기", ATMOS_OPTIONS, index=ATMOS_OPTIONS.index(
                        u['preferred_atmosphere']), key=f"edit_atmos_{sel}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("저장 변경", key=f"save_user_{sel}"):
                            if is_duplicate_user(new_name, new_region, users, exclude_id=sel):
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
                        if st.button("삭제", key=f"del_user_{sel}"):
                            users = [x for x in users if x['id'] != sel]
                            save_users(users)
                            st.warning("삭제됨 (매칭 재실행 필요)")
                            st.rerun()
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
        run_ids = sorted({c.get('match_run_id', '')
                         for c in clubs_all if c.get('match_run_id')}, reverse=True)
        if run_ids:
            selected_run = st.selectbox("Match Run 선택", options=run_ids)
            clubs = [c for c in clubs_all if c.get(
                'match_run_id') == selected_run]
        else:
            st.warning("Run ID 없는 클럽만 존재. 전체 표시")
            clubs = clubs_all
        st.caption(f"클럽 수: {len(clubs)}")
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
        for c in clubs:
            with st.expander(f"클럽 {c['id']} | 인원 {len(c['member_ids'])} | 상태 {c.get('status', '?')}"):
                st.write("리더:", c['leader_id'])
                st.write("멤버:", ', '.join(c['member_ids']))
                st.json(c['match_score_breakdown'])
                # Explanations table
                exp = c.get('explanations') or {}
                if exp:
                    with st.expander("매칭 설명"):
                        for uid, peers in exp.items():
                            st.write(
                                f"{uid} → " + '; '.join(f"{pid}:{reason}" for pid, reason in peers.items()))
                leader_input = st.text_input(
                    f"리더 ID 확인 ({c['id']})", key=f"leader_check_{c['id']}")
                if leader_input == c['leader_id'] and c.get('status') == 'Matched':
                    chat_url = st.text_input(
                        f"채팅 링크 입력 ({c['id']})", key=f"chat_{c['id']}")
                    if chat_url and st.button(f"활성화 ({c['id']})"):
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
        for c in clubs_all:
            with st.expander(f"클럽 {c['id']} | 인원 {len(c['member_ids'])} | 상태 {c.get('status', '?')}"):
                st.write("리더:", c['leader_id'])
                st.write("멤버:", ', '.join(c['member_ids']))
                st.json(c['match_score_breakdown'])

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
    st.dataframe(load_users(), use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.caption(
    f"Data dir: data | {dt.datetime.now(dt.timezone.utc).strftime('%H:%M:%S')}Z")
