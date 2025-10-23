import streamlit as st
import time
import os

from services import activity, persistence
from services.admin import get_user_map


def render_verification_tab():
    """Allows admins to verify pending activity reports."""
    st.subheader("✅ 활동 보고서 검증")

    reports = activity.list_reports()
    clubs_map = {c['id']: c for c in persistence.load_list('clubs')}
    pending = [r for r in reports if r['status'] == 'Pending']

    if not pending:
        st.info("검증 대기 중인 보고서가 없습니다.")
    else:
        st.write(f"**{len(pending)}**개의 보고서가 검증을 기다리고 있습니다.")
        for r in pending:
            club = clubs_map.get(r['club_id'])
            club_name = club.get('name', '') if club else ''
            title = f"Report {r['id']} | Club {club_name or '(이름없음)'} ({r['club_id']}) | Date: {r['date']}"
            with st.expander(title):
                raw_text = r.get('raw_text', '')
                participants = r.get('participant_override')
                participants_disp = participants if participants not in (
                    None, '', 'N/A') else '미기재'
                st.markdown(f"""
**보고서 내용**
- **활동일자:** {r.get('date','-')}
- **참여인원:** {participants_disp}
- **활동내용:**
  {raw_text}
""")
                # Show attached image if photo filename present and file exists in static/
                photo_name = r.get('photo_filename')

                def resolve_image(name: str) -> str:
                    placeholders = {'', 'no_photo', 'none',
                                    'empty', 'null', 'placeholder'}
                    base_dir = os.getcwd()
                    static_dir = os.path.join(base_dir, 'static')
                    target = name
                    if not target or str(target).lower() in placeholders:
                        target = 'image.png'
                    path = os.path.join(static_dir, target)
                    if not os.path.exists(path):
                        # try parent
                        parent_static = os.path.abspath(
                            os.path.join(base_dir, '..', 'static'))
                        alt = os.path.join(parent_static, target)
                        if os.path.exists(alt):
                            path = alt
                    return path
                if photo_name:
                    img_path = resolve_image(photo_name)
                    if os.path.exists(img_path):
                        half_cols = st.columns([1, 1])
                        with half_cols[0]:
                            st.image(
                                img_path, caption=f"첨부 사진: {os.path.basename(img_path)}", use_container_width=True)
                    else:
                        st.caption(f"첨부 사진 파일을 찾을 수 없음: {img_path}")
                preview = r.get('verification_preview')
                if not preview:
                    if st.button("AI 검증 실행", key=f"prepare_{r['id']}"):
                        with st.spinner("검증 중..."):
                            time.sleep(1)
                            preview_created = activity.prepare_report_verification(
                                r['id'])
                            # Run mock image analysis immediately if photo present
                            if r.get('photo_filename'):
                                activity.analyze_report_image(r['id'])
                        st.rerun()
                else:
                    metrics = preview.get('metrics', {})
                    thresholds = preview.get('thresholds', {})
                    passed = preview.get('passed', False)
                    label_map = {"participants": "참여",
                                 "interest": "관심사", "diversity": "다양성"}
                    detail_lines = []
                    for key, threshold in thresholds.items():
                        raw_val = metrics.get(key, 0)
                        val_pct = int(round(raw_val * 100))
                        thr_pct = int(round(threshold * 100))
                        status_ok = raw_val >= threshold
                        status_txt = "충족" if status_ok else "미달"
                        badge_color = "#16a34a" if status_ok else "#dc2626"
                        badge_html = f"<span style='color:#fff; background:{badge_color}; padding:2px 6px; border-radius:12px; font-size:11px;'>{status_txt}</span>"
                        detail_lines.append(
                            f"- **{label_map.get(key, key)}**: {val_pct} / {thr_pct} {badge_html}")
                    st.info("미리보기 생성됨. 확인 후 최종 검증을 진행하세요.")
                    preview_block = """**세부 지표**\n{}\n- **예상 포인트:** {}\n- 점수 산출 기준: 참여율(클럽 전체 대비), 보고서 내 관심사 키워드 언급 비율, 참여자 직급 다양성 비율을 각각 기준치와 비교합니다.""".format(
                        "\n".join(detail_lines), preview.get('points_if_finalized', 0))
                    st.markdown(preview_block, unsafe_allow_html=True)
                    # Mock image analysis trigger
                    if r.get('photo_filename'):
                        ia_prev = preview.get(
                            'image_analysis') if preview else None
                        if ia_prev:
                            st.caption(
                                f"이미지 분석 태그: {', '.join(ia_prev.get('tags', []))} | 관련도 {int(ia_prev.get('relevance_score',0)*100)}% | 안전성 {ia_prev.get('safety','-')}")
                            st.caption(ia_prev.get('commentary', ''))
                        else:
                            if st.button("이미지 분석 실행", key=f"img_analyze_prev_{r['id']}"):
                                with st.spinner("이미지 분석 중 (모의)..."):
                                    activity.analyze_report_image(r['id'])
                                st.rerun()
                    if metrics.get('interest', 0) == 0:
                        st.warning(
                            "관심사 지표가 0입니다: 보고 내용에 클럽 구성원의 관심사 키워드가 하나도 포함되지 않았습니다. 활동 설명에 관심사 관련 단어를 추가하면 점수가 상승할 수 있습니다.")
                    col_prev1, col_prev2 = st.columns(2)
                    with col_prev1:
                        if st.button("최종 검증 확정", key=f"finalize_{r['id']}"):
                            ok = activity.finalize_report_verification(r['id'])
                            if ok:
                                st.success("최종 검증 완료")
                                st.rerun()
                            else:
                                st.error("검증 확정 실패")
                    with col_prev2:
                        if st.button("취소", key=f"cancel_preview_{r['id']}"):
                            # Remove preview without verifying
                            reports_all = activity.list_reports()
                            rep_obj = next(
                                (rp for rp in reports_all if rp['id'] == r['id']), None)
                            if rep_obj and 'verification_preview' in rep_obj:
                                del rep_obj['verification_preview']
                                from services import persistence as _p
                                _p.replace_all('activity_reports', reports_all)
                            st.rerun()

    st.divider()
    st.subheader("검증 완료된 보고서")
    verified = [r for r in reports if r['status'] == 'Verified']
    if not verified:
        st.info("검증 완료된 보고서가 아직 없습니다.")
    else:
        for vr in verified:
            metrics = vr.get('verification_metrics', {})
            club = clubs_map.get(vr['club_id'])
            club_name = club.get('name', '') if club else ''
            with st.expander(f"✅ {vr['id']} | Club {club_name or '(이름없음)'} ({vr['club_id']}) | Date {vr['date']}"):
                raw_text_v = vr.get('raw_text', '')
                participants_v = vr.get('participant_override')
                part_ids = vr.get('participant_ids') or []
                if part_ids:
                    participants_v = len(part_ids)
                participants_v_disp = participants_v if participants_v not in (
                    None, '', 'N/A') else '미기재'
                st.markdown(
                    f"""
**보고서 내용**
- **활동일자:** {vr.get('date','-')}
- **참여인원:** {participants_v_disp}
- **활동내용:**
  {raw_text_v}
"""
                )
                # Display verified report image if available
                photo_v = vr.get('photo_filename')
                if photo_v:
                    def resolve_verified(name: str) -> str:
                        placeholders = {'', 'no_photo', 'none',
                                        'empty', 'null', 'placeholder'}
                        base_dir_v = os.getcwd()
                        static_dir_v = os.path.join(base_dir_v, 'static')
                        tgt = name
                        if not tgt or str(tgt).lower() in placeholders:
                            tgt = 'image.png'
                        pth = os.path.join(static_dir_v, tgt)
                        if not os.path.exists(pth):
                            parent_static_v = os.path.abspath(
                                os.path.join(base_dir_v, '..', 'static'))
                            alt_v = os.path.join(parent_static_v, tgt)
                            if os.path.exists(alt_v):
                                pth = alt_v
                        return pth
                    img_v_path = resolve_verified(photo_v)
                    if os.path.exists(img_v_path):
                        half_cols_v = st.columns([1, 1])
                        with half_cols_v[0]:
                            st.image(
                                img_v_path, caption=f"첨부 사진: {os.path.basename(img_v_path)}", use_container_width=True)
                    else:
                        st.caption(f"첨부 사진 파일을 찾을 수 없음: {img_v_path}")
                cols = st.columns(3)
                cols[0].metric(
                    '참여', f"{int(round(metrics.get('participants',0)*100))}")
                cols[1].metric(
                    '관심사', f"{int(round(metrics.get('interest',0)*100))}")
                cols[2].metric(
                    '다양성', f"{int(round(metrics.get('diversity',0)*100))}")
                thresholds = {"participants": 0.75,
                              "interest": 0.70, "diversity": 0.60}
                label_map = {"participants": "참여",
                             "interest": "관심사", "diversity": "다양성"}
                reason_bits = []
                for k, v in thresholds.items():
                    raw_val = metrics.get(k, 0)
                    val_pct = int(round(raw_val*100))
                    thr_pct = int(round(v*100))
                    status_ok = raw_val >= v
                    status = "충족" if status_ok else "미달"
                    badge_color = "#16a34a" if status_ok else "#dc2626"
                    badge_html = f"<span style='color:#fff; background:{badge_color}; padding:2px 6px; border-radius:10px; font-size:10px;'>{status}</span>"
                    reason_bits.append(
                        f"{label_map.get(k,k)} {val_pct}/{thr_pct} {badge_html}")
                # reason_txt removed (unused) after label_map introduction
                photo_attached = "예" if vr.get('photo_filename') else "아니오"
                st.caption(
                    f"Points: {vr.get('points_awarded', 0)} | Verified at: {vr.get('verified_at', '-')} | 사진 첨부여부: {photo_attached}")
                verified_block = """**세부 지표**\n{}\n- 점수 산출 기준: 참여율·관심사·직급 다양성 3가지 지표를 기준치와 비교합니다.""".format(
                    "\n".join([f"- {b}" for b in reason_bits]))
                st.markdown(verified_block, unsafe_allow_html=True)
                # Display image analysis or allow trigger (post-verification)
                if vr.get('photo_filename'):
                    ia = vr.get('image_analysis')
                    if ia:
                        st.caption(
                            f"이미지 분석 태그: {', '.join(ia.get('tags', []))} | 관련도 {int(ia.get('relevance_score',0)*100)}% | 안전성 {ia.get('safety','-')}")
                        st.caption(ia.get('commentary', ''))
                    else:
                        if st.button("이미지 분석 실행", key=f"img_analyze_v_{vr['id']}"):
                            with st.spinner("이미지 분석 중 (모의)..."):
                                activity.analyze_report_image(vr['id'])
                            st.rerun()
                if metrics.get('interest', 0) == 0:
                    st.warning("관심사 지표가 0입니다: 보고 내용에 클럽 관심사 키워드가 포함되지 않았습니다.")
                # Hidden control inside details-like block
                # Lightweight details/ellipsis control
                st.markdown(
                    f"""
<details style='margin-top:0.5rem;'>
  <summary style='cursor:pointer;'>추가 작업(⋯)</summary>
  <small>검증을 되돌리면 상태가 Pending으로 돌아갑니다.</small><br/>
  <form>
  </form>
""", unsafe_allow_html=True)
                if st.button("되돌리기 (Un-Verify)", key=f"btn_unverify_{vr['id']}"):
                    ok = activity.unverify_report(vr['id'])
                    if ok:
                        st.success("보고서 상태가 Pending으로 변경되었습니다.")
                        st.rerun()
                    else:
                        st.error("되돌리기에 실패했습니다.")
