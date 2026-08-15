import time
import requests
from typing import List
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper, JobListing

class Big4Scraper(BaseScraper):
    """Scraper tailored for the Big 4 consulting firms restricted to India. Uses HTTP requests to bypass UI headless detection."""

    @property
    def source_name(self) -> str:
        return "Big4"

    def _is_india_location(self, loc: str) -> bool:
        if not loc:
            return False
        loc_lower = loc.lower()
        indian_keywords = {
            "india", "bangalore", "bengaluru", "hyderabad", "pune", "mumbai", 
            "delhi", "noida", "gurgaon", "gurugram", "chennai", "kolkata", 
            "ahmedabad", "jaipur", "chandigarh", "kochi", "thiruvananthapuram"
        }
        return any(k in loc_lower for k in indian_keywords)

    def scrape(self, keywords: str, location: str, max_pages: int = 1) -> List[JobListing]:
        jobs = []
        
        print(f"  [Big4] Starting dedicated Big 4 search for '{keywords}' in India...")
        
        session = requests.Session()
        session.headers.update(self._get_headers())

        # Scrape Deloitte
        try:
            jobs.extend(self._scrape_deloitte(session, keywords))
        except Exception as e:
            print(f"  [Big4 - Deloitte] Error: {e}")

        # Scrape PwC
        try:
            jobs.extend(self._scrape_pwc(session, keywords))
        except Exception as e:
            print(f"  [Big4 - PwC] Error: {e}")

        # Scrape EY
        try:
            jobs.extend(self._scrape_ey(session, keywords))
        except Exception as e:
            print(f"  [Big4 - EY] Error: {e}")

        # Scrape KPMG
        try:
            jobs.extend(self._scrape_kpmg(session, keywords))
        except Exception as e:
            print(f"  [Big4 - KPMG] Error: {e}")

        print(f"  [Big4] Completed. Found {len(jobs)} jobs in India across Big 4.")
        return jobs

    def _scrape_deloitte(self, session: requests.Session, keywords: str) -> List[JobListing]:
        jobs = []
        search_kw = quote_plus(keywords)
        url = f"https://apply.deloitte.com/careers/SearchJobs/?keyword={search_kw}"
        
        print(f"  [Big4 - Deloitte] Searching: {url}")
        
        headers = {"X-Requested-With": "XMLHttpRequest"}
        resp = session.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            print(f"  [Big4 - Deloitte] No job cards found or timed out. Status: {resp.status_code}")
            return jobs

        soup = BeautifulSoup(resp.text, "lxml")
        job_elements = soup.select(".article__item, .list-unstyled > li, .job-item")
        
        for elem in job_elements:
            title_el = elem.select_one("h3 a, a.job-title, h4 a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            job_url = title_el.get("href", "")
            if job_url and not job_url.startswith("http"):
                job_url = "https://apply.deloitte.com" + job_url
                
            loc_el = elem.select_one(".location, .list-inline span, .job-location")
            job_loc = loc_el.get_text(strip=True) if loc_el else "India"
            
            if self._is_india_location(job_loc) or "india" in title.lower() or "india" in job_loc.lower():
                jobs.append(JobListing(
                    title=title,
                    company="Deloitte",
                    location=job_loc,
                    description="",
                    url=job_url,
                    source=self.source_name
                ))
                
        print(f"  [Big4 - Deloitte] Found {len(jobs)} jobs.")
        return jobs

    def _scrape_pwc(self, session: requests.Session, keywords: str) -> List[JobListing]:
        jobs = []
        url = "https://pwc.wd3.myworkdayjobs.com/wday/cxs/pwc/Global_Experienced_Careers/jobs"
        print(f"  [Big4 - PwC] Searching: {url}")
        
        payload = {
            "appliedFacets": {},
            "limit": 20,
            "offset": 0,
            "searchText": keywords
        }
        
        resp = session.post(
            url, 
            json=payload, 
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=15
        )
        
        if resp.status_code == 200:
            data = resp.json()
            postings = data.get("jobPostings", [])
            for job in postings:
                title = job.get("title", "")
                external_path = job.get("externalPath", "")
                job_url = f"https://pwc.wd3.myworkdayjobs.com/en-US/Global_Experienced_Careers{external_path}"
                job_loc = job.get("locationsText", "India")
                
                if self._is_india_location(job_loc) or "india" in title.lower() or "bangalore" in job_url.lower() or "mumbai" in job_url.lower():
                    jobs.append(JobListing(
                        title=title,
                        company="PwC",
                        location=job_loc,
                        description="",
                        url=job_url,
                        source=self.source_name
                    ))
        else:
            print(f"  [Big4 - PwC] Failed with status {resp.status_code}")
            
        print(f"  [Big4 - PwC] Found {len(jobs)} jobs.")
        return jobs

    def _scrape_ey(self, session: requests.Session, keywords: str) -> List[JobListing]:
        jobs = []
        search_kw = quote_plus(keywords)
        url = f"https://careers.ey.com/ey/search/?q={search_kw}&locationsearch=India"
        print(f"  [Big4 - EY] Searching: {url}")
        
        resp = session.get(url, timeout=15)
        if resp.status_code != 200:
            print(f"  [Big4 - EY] Failed with status {resp.status_code}")
            return jobs
            
        soup = BeautifulSoup(resp.text, "lxml")
        job_rows = soup.select(".searchResultsShell table tr.data-row")
        for row in job_rows:
            title_el = row.select_one(".jobTitle a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            job_url = title_el.get("href", "")
            if job_url and not job_url.startswith("http"):
                job_url = "https://careers.ey.com" + job_url
                
            loc_el = row.select_one(".jobLocation")
            job_loc = loc_el.get_text(strip=True) if loc_el else "India"
            job_loc = job_loc.replace(r"\n", "").strip()
            
            if self._is_india_location(job_loc) or "india" in title.lower():
                jobs.append(JobListing(
                    title=title,
                    company="EY",
                    location=job_loc,
                    description="",
                    url=job_url,
                    source=self.source_name
                ))
                
        print(f"  [Big4 - EY] Found {len(jobs)} jobs.")
        return jobs

    def _scrape_kpmg(self, session: requests.Session, keywords: str) -> List[JobListing]:
        jobs = []
        print(f"  [Big4 - KPMG] Bypassing Oracle HCM strictly protected token wall.")
        # To maintain stability, we skip KPMG Oracle HCM complex token handshake for now.
        return jobs
