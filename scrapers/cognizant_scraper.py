import time
from typing import List
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from scrapers.base_scraper import BaseScraper, JobListing

class CognizantScraper(BaseScraper):
    @property
    def source_name(self) -> str:
        return "Cognizant"

    def scrape(self, keywords: str, location: str, max_pages: int = 3) -> List[JobListing]:
        jobs = []
        # Construct the URL for the first page
        base_url = f"https://careers.cognizant.com/global/en/search-results?keywords={quote_plus(keywords)}"
        
        print(f"  [Cognizant] Searching: '{keywords}' in '{location}' (Playwright)...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=self._get_headers()["User-Agent"])
            page = context.new_page()

            # For simplicity we loop through pages assuming phenom pagination (&from=0, &from=10).
            # Each page typically has 10 cards.
            for page_num in range(max_pages):
                offset = page_num * 10
                url = base_url if page_num == 0 else f"{base_url}&from={offset}&s=1"
                
                try:
                    page.goto(url, wait_until="networkidle", timeout=30000)
                    # Handle cookie banner that might obstruct if needed, though usually not blocking the DOM
                    try:
                        page.wait_for_selector(".card.card-job", timeout=15000)
                    except:
                        print(f"  [Cognizant] No job cards found on page {page_num+1} (Timeout).")
                        break
                        
                    time.sleep(2) # Give it a moment to fully render list
                    
                    html = page.content()
                    soup = BeautifulSoup(html, "lxml")
                    
                    cards = soup.select(".card.card-job")
                    print(f"  [Cognizant] Page {page_num+1}: found {len(cards)} cards")
                    
                    if len(cards) == 0:
                        break
                    
                    for card in cards:
                        title_elem = card.select_one(".card-title a")
                        title = title_elem.get_text(strip=True) if title_elem else "Unknown"
                        
                        loc_elem = card.select_one(".job-meta li.list-inline-item:first-child")
                        job_loc = loc_elem.get_text(strip=True) if loc_elem else "India"
                        
                        link_elem = card.select_one("a.stretched-link") or card.select_one("a.js-view-job")
                        job_url = "https://careers.cognizant.com" + link_elem["href"] if link_elem and link_elem.has_attr("href") else base_url
                        
                        if location.lower() not in job_loc.lower() and location.lower() != "india" and job_loc.lower() != "multiple locations":
                            continue
                            
                        jobs.append(JobListing(
                            title=title,
                            company="Cognizant",
                            location=job_loc,
                            description="",
                            url=job_url,
                            source=self.source_name
                        ))
                except Exception as e:
                    print(f"  [Cognizant] Error fetching jobs on page {page_num+1}: {e}")
                    break
                    
            browser.close()

        return jobs
