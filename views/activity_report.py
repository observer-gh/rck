import streamlit as st
from services import activity, persistence
from ui.components import report_card, status_badge, dataframe_with_status
import pandas as pd
from io import StringIO
from typing import Optional  # Python 3.9 compatibility for Optional[str]
import datetime as _dt


def _club_options(current_user_id: Optional[str]):
    clubs_all = persistence.load_list('clubs')
    active_clubs = [c for c in clubs_all if c.get('status') == 'Active']
    # Auto-upgrade matched clubs to Active for demo convenience if user has only Matched
    if not active_clubs and current_user_id:
        matched_user_clubs = [c for c in clubs_all if c.get(
            'status') == 'Matched' and current_user_id in c.get('member_ids', [])]
        if matched_user_clubs:
            for c in matched_user_clubs:
                c['status'] = 'Active'
            persistence.replace_all('clubs', clubs_all)
            active_clubs = matched_user_clubs
    if not active_clubs:
        return []
    users = persistence.load_list('users')
    user_map = {u['id']: u for u in users}
    # If user context exists, limit to their clubs
    if current_user_id:
        active_clubs = [
            c for c in active_clubs if current_user_id in c.get('member_ids', [])]
    options = []
    for c in active_clubs:
        leader_id = c.get('leader_id')
        club_nm = c.get('name') or (user_map.get(
            leader_id, {}).get('name', 'N/A') + " 팀")
        options.append(f"{c['id']} - {club_nm}")
    return options


def view():
    st.header("활동 보고서 제출")
    # 데모 패널 제거로 깔끔한 기본 제출 화면 유지
    current_user_id = getattr(st.session_state, 'current_user_id', None)
    club_options = _club_options(current_user_id)
    if not club_options:
        st.warning("활동 보고서를 제출할 수 있는 'Active' 상태의 (내) 클럽이 없습니다.")
        return  # Prevent form rendering that relies on initialized session keys
    choice = st.selectbox("클럽 선택", options=club_options)
    if not choice:
        st.stop()
    club_id = str(choice).split()[0]
    st.session_state.selected_club_id = club_id
    # Global prefill/session key initialization (runs regardless of club state)
    if 'prefill_date' not in st.session_state:
        st.session_state.prefill_date = _dt.date.today()
    st.session_state.setdefault('prefill_report_text', "")
    st.session_state.setdefault('prefill_participants', 0)
    st.session_state.setdefault(
        'report_raw_text', st.session_state.prefill_report_text)
    st.session_state.setdefault(
        'report_participants', st.session_state.prefill_participants)

    # File uploader outside form for immediate preview
    photo = st.file_uploader("사진 업로드 (시뮬레이션)", key="report_photo")
    if photo is not None:
        try:
            from PIL import Image
            image = Image.open(photo)
            # Target half of typical content width (~600px if full ~1200px)
            target_width = 600
            w, h = image.size
            if w > target_width:
                ratio = target_width / float(w)
                image = image.resize((int(w * ratio), int(h * ratio)))
            col_prev, col_spacer = st.columns([1, 1])
            with col_prev:
                st.image(image, caption=f"업로드된 사진: {photo.name}")
        except Exception as _e:
            st.warning(f"이미지 미리보기 실패: {_e}")

    # Keep form values after submission so auto-fill results remain visible
    with st.form("activity_report_form", clear_on_submit=False):
        date = st.date_input("활동 날짜", key="report_date",
                             value=st.session_state.prefill_date)
        # Auto-fill trigger (button always visible now)
        autofill_triggered = False
        if st.form_submit_button("사진 기반 자동 채우기", type="secondary"):
            import time
            with st.spinner("사진 분석 중…"):
                # Simulated incremental progress over ~2.3s (faster UX but still perceptible)
                prog = st.progress(0)
                total_seconds = 2.3
                steps = 23  # 0.1s per step
                for i in range(steps):
                    time.sleep(total_seconds/steps)
                    prog.progress(int((i+1)/steps*100))
            # Hard-coded demo values (updated narrative reflecting team speed/agility drill)
            st.session_state.prefill_report_text = (
                "야외 잔디에서 스피드·코디네이션 드릴 진행. 동시 스타트 스프린트와 페이스 맞추기 반복으로 집중도 상승, "
                "구성원 간 콜과 격려 자연스럽게 형성. 마무리 후 다음 모임에 미니게임+회복 스트레칭 블록 추가 계획.")
            # Dynamic participant count based on current club membership (fallback 6 for demo baseline)
            club_id = st.session_state.get('selected_club_id')
            member_count = 0
            if club_id:
                try:
                    clubs_all = persistence.load_list('clubs')
                    club_obj = next(
                        (c for c in clubs_all if c.get('id') == club_id), None)
                    if club_obj:
                        member_count = len(
                            club_obj.get('member_ids', []) or [])
                except Exception:
                    member_count = 0
            if member_count <= 0:
                member_count = 6  # demo fallback size
            st.session_state.prefill_participants = member_count
            st.session_state.prefill_date = date  # keep chosen date
            # Synchronize widget-bound keys so values appear immediately after rerun
            st.session_state.report_raw_text = st.session_state.prefill_report_text
            st.session_state.report_participants = st.session_state.prefill_participants
            # Do not set report_date here; widget already instantiated (would raise StreamlitAPIException)
            autofill_triggered = True
            st.rerun()
        raw_text = st.text_area(
            "활동 내용", key="report_raw_text")
        part_count = st.number_input(
            "참여 인원(선택)", min_value=0, max_value=100, key="report_participants")
        submitted = st.form_submit_button("보고서 제출")
        # Removed completion info banner for cleaner UI (spinner/progress already gives feedback)
        if submitted:
            if not raw_text:
                st.error("활동 내용을 입력해주세요.")
            else:
                photo_name = photo.name if photo is not None else 'no_photo'
                rep = activity.create_activity_report(
                    club_id=club_id,
                    date=str(date),
                    photo_name=photo_name,
                    raw_text=raw_text,
                    participant_override=part_count if part_count > 0 else None,
                )
                st.success(f"보고서 생성 완료. ID: {rep.id}")
    st.divider()
    st.subheader("내가 제출한 보고서")
    reports = activity.list_reports()
    if not reports:
        st.caption("아직 제출한 보고서가 없습니다.")
        return
    if current_user_id:
        user_club_ids = {c['id'] for c in persistence.load_list(
            'clubs') if current_user_id in c.get('member_ids', [])}
        reports = [r for r in reports if r['club_id'] in user_club_ids]
    if not reports:
        st.caption("표시할 보고서가 없습니다.")
        return
    colf1, colf2, colf3 = st.columns([2, 2, 1])
    unique_dates = sorted({r['date'] for r in reports})
    date_filter = colf1.selectbox("날짜 필터", ["(전체)"] + unique_dates)
    status_filter = colf2.selectbox("상태 필터", ["(전체)", "Pending", "Verified"])
    search_text = colf3.text_input("검색", placeholder="키워드")
    if 'report_view_mode' not in st.session_state:
        st.session_state.report_view_mode = "카드"
    view_mode = st.radio("표시 형식", ["카드", "테이블"],
                         horizontal=True, key="report_view_mode")
    filtered = reports
    if date_filter != "(전체)":
        filtered = [r for r in filtered if r['date'] == date_filter]
    if status_filter != "(전체)":
        filtered = [r for r in filtered if r['status'] == status_filter]
    if search_text:
        lowered = search_text.lower()
        filtered = [r for r in filtered if lowered in r.get(
            'raw_text', '').lower() or lowered in r.get('formatted_report', '').lower()]
    if not filtered:
        st.info("필터 조건에 해당하는 보고서가 없습니다.")
        return
    if view_mode == "테이블":
        df = pd.DataFrame([
            {
                'id': r['id'], 'date': r['date'], 'status': r['status'], 'points': r.get('points_awarded', 0),
                'club_id': r['club_id'], 'photo': r.get('photo_filename', ''), '요약': (r.get('formatted_report', '')[:60] + '…') if len(r.get('formatted_report', '')) > 60 else r.get('formatted_report', '')
            } for r in filtered
        ])
        dataframe_with_status(df, status_col='status')
        with st.expander("전체 내용 보기 / Export"):
            for r in filtered:
                st.markdown(
                    f"**{r['id']}** {status_badge(r['status'])}", unsafe_allow_html=True)
                st.caption(r.get('formatted_report', ''))
                st.write("---")
            csv_buf = StringIO()
            pd.DataFrame(filtered).to_csv(csv_buf, index=False)
            st.download_button("CSV 다운로드", data=csv_buf.getvalue(
            ), file_name="reports.csv", mime="text/csv")
    else:
        sorted_reports = sorted(
            filtered, key=lambda r: r['date'], reverse=True)
        for r in sorted_reports:
            report_card(r)
        csv_buf = StringIO()
        pd.DataFrame(sorted_reports).to_csv(csv_buf, index=False)
        st.download_button("(필터) CSV 다운로드", data=csv_buf.getvalue(),
                           file_name="reports.csv", mime="text/csv")
