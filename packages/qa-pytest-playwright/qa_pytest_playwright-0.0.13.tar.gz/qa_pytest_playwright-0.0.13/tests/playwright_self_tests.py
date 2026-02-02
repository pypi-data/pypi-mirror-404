import pytest


@pytest.mark.ui
def should_open_browser():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-gpu"])
        page = browser.new_page()

        try:
            page.goto("https://www.terminalx.com", timeout=60000)
            page.wait_for_load_state("domcontentloaded")
            assert "terminal x" in page.title().lower()
        finally:
            browser.close()
