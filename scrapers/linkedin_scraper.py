"""
LinkedIn Jobs scraper — Extracts job listings from LinkedIn's guest job search.
No login required; uses the publicly accessible search API.
"""
from typing import List
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper, JobListing


class LinkedInScraper(BaseScraper):
    """Scrapes job listings from LinkedIn Jobs (guest/public access)."""

    BASE_URL = "https://www.linkedin.com/jobs/search"

    @property
    def source_name(self) -> str:
        return "linkedin"

    def _build_search_url(self, keywords: str, location: str, start: int = 0) -> str:
        """Build LinkedIn guest job search URL."""
        params = {
            "keywords": keywords,
            "location": location,
            "trk": "public_jobs_jobs-search-bar_search-submit",
            "position": 1,
            "pageNum": 0,
            "start": start,
            "f_TPR": "r604800"  # Past 7 days
        }
        query = "&".join(f"{k}={quote_plus(str(v))}" for k, v in params.items())
        return f"{self.BASE_URL}?{query}"

    def _parse_job_card(self, card) -> JobListing:
        """Parse a single LinkedIn job card."""
        title_el = card.select_one(
            "h3.base-search-card__title, "
            ".base-search-card__title, "
            "h3[class*='job-title'], "
            "span[class*='job-title']"
        )
        company_el = card.select_one(
            "h4.base-search-card__subtitle a, "
            ".base-search-card__subtitle, "
            "a[class*='company-name']"
        )
        location_el = card.select_one(
            "span.job-search-card__location, "
            ".base-search-card__metadata span, "
            "span[class*='location']"
        )
        date_el = card.select_one(
            "time, "
            "span.job-search-card__listdate, "
            "span[class*='listed-date']"
        )
        link_el = card.select_one(
            "a.base-card__full-link, "
            "a[class*='base-card'], "
            "a[href*='/jobs/view/']"
        )

        title = title_el.get_text(strip=True) if title_el else "Unknown"
        company = company_el.get_text(strip=True) if company_el else "Unknown"
        location = location_el.get_text(strip=True) if location_el else ""
        posted_date = date_el.get("datetime", date_el.get_text(strip=True)) if date_el else ""

        url = ""
        if link_el:
            url = link_el.get("href", "")
        if not url:
            # Try finding any link to a job page
            any_link = card.select_one("a[href*='/jobs/']")
            url = any_link.get("href", "") if any_link else ""

        # Clean URL (remove tracking params)
        if "?" in url:
            url = url.split("?")[0]

        return JobListing(
            title=title,
            company=company,
            location=location,
            description="",  # LinkedIn doesn't show full desc in search
            url=url,
            source=self.source_name,
            posted_date=posted_date,
        )

    def scrape(self, keywords: str, location: str, max_pages: int = 3) -> List[JobListing]:
        """Scrape LinkedIn Jobs guest search."""
        all_jobs: List[JobListing] = []
        print(f"  [LinkedIn] Searching: '{keywords}' in '{location}'...")

        for page in range(max_pages):
            start = page * 25  # LinkedIn uses 25 results per page
            url = self._build_search_url(keywords, location, start)
            html = self._fetch(url)
            if not html:
                print(f"  [LinkedIn] Failed to fetch page {page + 1}, stopping.")
                break

            soup = BeautifulSoup(html, "lxml")

            # LinkedIn guest job cards
            cards = soup.select(
                "div.base-card, "
                "li.result-card, "
                "div.job-search-card, "
                "div[class*='base-search-card']"
            )

            if not cards:
                print(f"  [LinkedIn] No job cards found on page {page + 1}, stopping.")
                break

            for card in cards:
                try:
                    job = self._parse_job_card(card)
                    if job.title != "Unknown" and job.url:
                        all_jobs.append(job)
                except Exception as e:
                    print(f"  [LinkedIn] Error parsing card: {e}")
                    continue

            print(f"  [LinkedIn] Page {page + 1}: found {len(cards)} cards, {len(all_jobs)} total jobs")

        return all_jobs
