from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # Go to the app
    page.goto("http://localhost:8501")
    page.wait_for_load_state("networkidle")

    # 1. Verify User Signup page
    page.get_by_test_id("stRadio").get_by_text("User Signup").click()
    page.screenshot(path="jules-scratch/verification/01_user_signup.png")

    # 2. Verify Matching (Admin) page
    page.get_by_test_id("stRadio").get_by_text("Matching (Admin)").click()
    page.screenshot(path="jules-scratch/verification/02_matching_admin.png")

    # 3. Verify Verification (Admin) page
    page.get_by_test_id("stRadio").get_by_text("Verification (Admin)").click()
    page.screenshot(path="jules-scratch/verification/03_verification_admin.png")

    # 4. Verify Analytics in sidebar
    page.get_by_test_id("stExpander").filter(has_text="Analytics").click()
    page.screenshot(path="jules-scratch/verification/04_analytics.png")

    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)