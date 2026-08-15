"""
Generic career page scraper — Crawls company career/jobs pages to find openings.
Uses heuristics to identify job listing links on arbitrary career pages.
"""
import re
from typing import List
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from scrapers.base_scraper import BaseScraper, JobListing


# Patterns that commonly indicate job listing links
JOB_URL_PATTERNS = [
    r"/jobs?/",
    r"/careers?/",
    r"/openings?/",
    r"/positions?/",
    r"/vacancies?/",
    r"/opportunities?/",
    r"/apply/",
    r"lever\.co/",
    r"greenhouse\.io/",
    r"workday\.com/",
    r"ashbyhq\.com/",
    r"boards\.greenhouse/",
    r"jobs\.smartrecruiters/",
]

# Keywords that indicate a link text is about a job posting
JOB_LINK_TEXT_KEYWORDS = [
    "engineer", "developer", "manager", "analyst", "designer", "lead",
    "architect", "scientist", "specialist", "coordinator", "intern",
    "associate", "consultant", "director", "administrator", "devops",
    "sre", "qa", "tester", "frontend", "backend", "fullstack",
    "full-stack", "full stack", "data", "cloud", "security", "product",
    "technical", "software", "web", "mobile", "android", "ios",
]


class CareerPageScraper(BaseScraper):
    """Scrapes job listings from company career pages."""

    # Domains that definitely need Playwright/JS rendering
    JS_REQUIRED_DOMAINS = [
        "cognizant.com", "tcs.com", "infosys.com", "wipro.com", 
        "accenture.com", "capgemini.com", "hcltech.com", 
        "ibm.com", "deloitte.com", "ey.com", "pwc.com", "kpmg.com",
        "oraclecloud.com", "workday.com", "lever.co"
    ]

    @property
    def source_name(self) -> str:
        return "career_page"

    def _is_job_link(self, href: str, text: str) -> bool:
        """Check if a link likely points to a job posting."""
        href_lower = (href or "").lower()
        text_lower = (text or "").lower().strip()

        # Check URL patterns
        for pattern in JOB_URL_PATTERNS:
            if re.search(pattern, href_lower):
                return True

        # Check link text for job-related keywords
        if len(text_lower) > 5:  # skip very short text
            for keyword in JOB_LINK_TEXT_KEYWORDS:
                if keyword in text_lower:
                    return True

        return False

    def _scrape_career_page(self, page_url: str, keywords: str) -> List[JobListing]:
        """Scrape a single career page for job listings."""
        parsed_base = urlparse(page_url)
        domain = parsed_base.netloc.lower()
        
        # Determine if we need JS rendering
        use_js = any(d in domain for d in self.JS_REQUIRED_DOMAINS)
        
        html = None
        if use_js:
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(user_agent=self._get_headers()["User-Agent"])
                    page = context.new_page()
                    page.goto(page_url, wait_until="networkidle", timeout=30000)
                    # Extra wait for dynamic content
                    page.wait_for_timeout(3000)
                    html = page.content()
                    browser.close()
            except Exception as e:
                print(f"  [CareerPage] Playwright error for {page_url}: {e}")
                # Fallback to requests
                html = self._fetch(page_url)
        else:
            html = self._fetch(page_url)

        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        jobs = []
        seen_urls = set()
        base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"

        # Find all links on the page
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            text = link.get_text(strip=True)

            if not text or len(text) < 3:
                # Check for aria-label or title if text is empty
                text = link.get("aria-label") or link.get("title") or ""
                if not text or len(text) < 3:
                    continue

            full_url = urljoin(page_url, href)
            if full_url in seen_urls:
                continue

            if self._is_job_link(href, text):
                # Check if keywords match (if provided)
                text_lower = text.lower()
                keywords_list = [kw.strip().lower() for kw in keywords.split(",") if kw.strip()]
                
                # Break full keywords into individual words (e.g. "java backend developer" -> "java", "backend", "developer")
                word_tokens = set()
                for kw in keywords_list:
                    word_tokens.update(kw.split())
                
                # Match if link text contains any of the core keywords (>3 chars) 
                match = not keywords_list or any(token in text_lower for token in word_tokens if len(token) > 3)
                
                if match:
                    seen_urls.add(full_url)
                    company = domain.replace("www.", "").split(".")[0].title()

                    jobs.append(JobListing(
                        title=text[:200],
                        company=company,
                        location="India", # Default to India as per config preference
                        description="",
                        url=full_url,
                        source=self.source_name,
                    ))

        return jobs

    def scrape(self, keywords: str, location: str, max_pages: int = 3,
               career_urls: List[str] = None) -> List[JobListing]:
        """
        Scrape company career pages for job listings.

        Args:
            keywords: Job search keywords
            location: Location (used for filtering only)
            max_pages: Not used for career pages
            career_urls: List of career page URLs to scrape

        Returns:
            List of JobListing objects
        """
        if not career_urls:
            print("  [CareerPage] No career page URLs configured. Skipping.")
            return []

        all_jobs: List[JobListing] = []
        print(f"  [CareerPage] Scanning {len(career_urls)} career pages...")

        for url in career_urls:
            try:
                print(f"  [CareerPage] Scanning: {url}")
                jobs = self._scrape_career_page(url, keywords)
                all_jobs.extend(jobs)
                print(f"  [CareerPage] Found {len(jobs)} listings on {url}")
            except Exception as e:
                print(f"  [CareerPage] Error scraping {url}: {e}")
                continue

        return all_jobs
