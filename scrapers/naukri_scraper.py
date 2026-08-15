import time
from typing import List
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page

from scrapers.base_scraper import BaseScraper, JobListing


class NaukriScraper(BaseScraper):
    """Scrapes job listings from Naukri.com using Playwright."""

    BASE_URL = "https://www.naukri.com"

    def __init__(self, rate_limit: float = 2.0, naukri_config=None):
        super().__init__(rate_limit)
        self.naukri_config = naukri_config

    @property
    def source_name(self) -> str:
        return "naukri"

    def _login(self, page: Page):
        """Perform login if credentials are provided."""
        if not self.naukri_config or not self.naukri_config.naukri_user or not self.naukri_config.naukri_password:
            return

        print(f"  [Naukri] Attempting login for {self.naukri_config.naukri_user}...")
        try:
            page.goto(f"{self.BASE_URL}/nlogin/login")
            page.wait_for_selector("#usernameField", timeout=10000)
            page.fill("#usernameField", self.naukri_config.naukri_user)
            page.fill("#passwordField", self.naukri_config.naukri_password)
            page.click("button[type='submit']")
            
            # Wait for login to complete (look for profile icon or similar)
            page.wait_for_load_state("networkidle")
            print("  [Naukri] Login successful (or redirected).")
        except Exception as e:
            print(f"  [Naukri] Login failed: {e}")

    def _build_search_url(self, keywords: str, location: str, page: int) -> str:
        """Build Naukri search URL."""
        kw_slug = keywords.lower().replace(" ", "-")
        loc_slug = location.lower().replace(" ", "-")
        url = f"{self.BASE_URL}/{kw_slug}-jobs-in-{loc_slug}"
        if page > 1:
            url += f"-{page}"
        url += "?jobAge=2"  # Request max 2 days old jobs from Naukri
        return url

    def scrape(self, keywords: str, location: str, max_pages: int = 3) -> List[JobListing]:
        """Scrape Naukri.com for job listings using Playwright."""
        all_jobs: List[JobListing] = []
        print(f"  [Naukri] Searching: '{keywords}' in '{location}' (Playwright)...")

        with sync_playwright() as p:
            # Use headless mode for compatibility with server environments
            # Use Edge if available for better local visibility
            browser = p.chromium.launch(
                headless=True,
                channel="msedge",
                args=['--disable-blink-features=AutomationControlled']
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            # Optional Login
            self._login(page)

            for p_num in range(1, max_pages + 1):
                url = self._build_search_url(keywords, location, p_num)
                print(f"  [Naukri] Fetching page {p_num}: {url}")
                
                try:
                    page.goto(url, wait_until="domcontentloaded")
                    # Wait for job tuples to appear
                    page.wait_for_selector(".srp-jobtuple-wrapper, article.jobTuple", timeout=10000)
                    
                    # Scroll down slowly to trigger lazy loading if needed
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
                    time.sleep(1)
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)

                    soup = BeautifulSoup(page.content(), "lxml")
                    cards = soup.select(".srp-jobtuple-wrapper, article.jobTuple")

                    if not cards:
                        print(f"  [Naukri] No job cards found on page {p_num}.")
                        break

                    for card in cards:
                        try:
                            job = self._parse_job_card(card)
                            if job.title != "Unknown" and job.url:
                                all_jobs.append(job)
                        except Exception as e:
                            continue

                    print(f"  [Naukri] Page {p_num}: found {len(cards)} cards")
                    
                    # Respect rate limit
                    time.sleep(self.rate_limit)

                except Exception as e:
                    print(f"  [Naukri] Error on page {p_num}: {e}")
                    break

            browser.close()

        return all_jobs

    def _parse_job_card(self, card) -> JobListing:
        """Parse a single job card element (reused from previous version)."""
        title_el = card.select_one("a.title, h2 a, .jobTupleHeader a, .title")
        company_el = card.select_one("a.subTitle, .companyInfo a, .comp-name, .subTitle")
        location_el = card.select_one(".locWdth, .loc-wrap, .location, .loc span, .locWdth span")
        exp_el = card.select_one(".expwdth, .exp-wrap, .experience, .exp span")
        desc_el = card.select_one(".job-description, .ellipsis, .job-desc")

        title = title_el.get_text(strip=True) if title_el else "Unknown"
        company = company_el.get_text(strip=True) if company_el else "Unknown"
        location = location_el.get_text(strip=True) if location_el else ""
        experience = exp_el.get_text(strip=True) if exp_el else ""
        description = desc_el.get_text(strip=True) if desc_el else ""

        url = ""
        if title_el and title_el.name == "a":
            url = title_el.get("href", "")
        elif title_el:
            link = title_el.find_parent("a") or card.select_one("a[href]")
            url = link.get("href", "") if link else ""

        if url and not url.startswith("http"):
            url = self.BASE_URL + url if url.startswith("/") else url

        skill_els = card.select(".tag-li, .skill, .chip, .tags-gt li, .dot-gt li")
        skills = [s.get_text(strip=True) for s in skill_els if s.get_text(strip=True)]

        return JobListing(
            title=title,
            company=company,
            location=location,
            description=description,
            url=url,
            source=self.source_name,
            experience=experience,
            skills=skills,
        )
