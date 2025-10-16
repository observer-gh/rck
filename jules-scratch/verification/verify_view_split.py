from playwright.sync_api import sync_playwright, expect

def run_verification():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Base URL for the Streamlit app
        base_url = "http://localhost:8501"

        # 1. Verify User View
        import time
        time.sleep(10) # Wait for streamlit to start
        page.goto(base_url)
        page.wait_for_selector("text='프로필/설문'")

        # Check that admin pages are not visible
        admin_dashboard_link = page.get_by_role("radio", name="어드민 대시보드")
        expect(admin_dashboard_link).not_to_be_visible()

        # Take a screenshot of the user view
        page.screenshot(path="jules-scratch/verification/01_user_view.png")

        # 2. Switch to Admin View
        admin_toggle = page.get_by_role("checkbox", name="Admin Mode")
        # Use JavaScript to click the element as a fallback
        admin_toggle.evaluate("el => el.click()")
        # Wait for the network to be idle, indicating the UI has likely finished updating.
        page.wait_for_load_state('networkidle')

        # Wait for the admin banner to appear
        expect(page.get_by_text("관리자 모드가 활성화되었습니다.")).to_be_visible()

        # Check that admin pages are now visible
        admin_dashboard_link = page.get_by_role("radio", name="어드민 대시보드")

        # Take a screenshot of the admin sidebar
        page.screenshot(path="jules-scratch/verification/02_admin_sidebar.png")

        # 3. Navigate to Admin Dashboard and check tabs
        # The click action has its own auto-wait, so we remove the explicit expect().to_be_visible()
        admin_dashboard_link.click()
        page.wait_for_selector("text='어드민 대시보드'")

        # Check that the tabs are rendered
        expect(page.get_by_role("tab", name="분석 및 현황")).to_be_visible()
        expect(page.get_by_role("tab", name="매칭 실행")).to_be_visible()
        expect(page.get_by_role("tab", name="클럽 관리")).to_be_visible()
        expect(page.get_by_role("tab", name="보고서 검증")).to_be_visible()
        expect(page.get_by_role("tab", name="데이터 관리")).to_be_visible()

        # Take a screenshot of the admin dashboard
        page.screenshot(path="jules-scratch/verification/03_admin_dashboard.png")

        browser.close()

if __name__ == "__main__":
    run_verification()