import re
from playwright.sync_api import sync_playwright

def test_naukri():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        print("Navigating to Naukri...")
        page.goto("https://www.naukri.com/python-jobs-in-india")
        
        # Wait for the job cards to load
        try:
            page.wait_for_selector(".srp-jobtuple-wrapper", timeout=10000)
            cards = page.query_selector_all(".srp-jobtuple-wrapper")
            print(f"Success! Found {len(cards)} job cards.")
            if cards:
                print("First card text:", cards[0].inner_text()[:100].replace('\n', ' | '))
        except Exception as e:
            print("Failed to find job cards:", e)
            print("Page title:", page.title())
            
        browser.close()

if __name__ == "__main__":
    test_naukri()
