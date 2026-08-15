from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time

def test_cognizant():
    url = "https://careers.cognizant.com/india/en/search-results?keywords=java"
    print(f"Testing {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=30000)
        time.sleep(5)  # Wait for JS to render the search results
        
        soup = BeautifulSoup(page.content(), "lxml")
        links = soup.select("a")
        
        jobs = []
        for l in links:
            href = l.get("href", "")
            text = l.get_text(strip=True).lower()
            if "java" in text or "developer" in text:
                jobs.append((text, href))
                
        print(f"Found {len(jobs)} potential job links on Cognizant:")
        for j in jobs:
            print(f" - {j}")
            
        browser.close()

if __name__ == "__main__":
    test_cognizant()
