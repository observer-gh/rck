from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    page.goto("http://localhost:8501/?sidebar=expanded")
    page.get_by_label("Admin Mode").check()
    page.get_by_text("어드민 대시보드").click()
    page.screenshot(path="jules-scratch/verification/admin_dashboard.png")
    browser.close()

with sync_playwright() as playwright:
    run(playwright)