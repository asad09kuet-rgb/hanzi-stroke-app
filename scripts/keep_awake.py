"""Open the Streamlit app in a headless browser and wake it if it is asleep."""
import os
import sys

from playwright.sync_api import sync_playwright

URL = os.environ["APP_URL"]

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(URL, wait_until="domcontentloaded", timeout=120_000)
    page.wait_for_timeout(8_000)
    wake = page.get_by_role("button", name="get this app back up", exact=False)
    if wake.count():
        print("App was asleep, waking it up")
        wake.first.click()
        page.wait_for_timeout(90_000)
    else:
        print("App is awake")
    title = page.title()
    print("Page title:", title)
    browser.close()
sys.exit(0)
