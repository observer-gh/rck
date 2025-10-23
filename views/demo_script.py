import streamlit as st


def view():
    """Simple demo guidance page (restored)."""
    st.header("데모 가이드")
    st.markdown(
        """
        ### 빠른 데모 흐름
        1. 데모 사용자 유지 / 필요 시 자동 동료 생성 (매칭 탭)
        2. 매칭 실행 후 클럽 활성화
        3. 활동 보고서 제출 → 관리자 검증
        4. 포인트 / 설명 확인

        상단 페이지들(내 클럽, 활동 보고)에서 데모 패널을 통해 즉시 시나리오를 체험할 수 있습니다.
        """
    )
