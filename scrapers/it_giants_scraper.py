import time
from typing import List
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
try:
    from playwright_stealth import Stealth
    HAS_STEALTH = True
except ImportError:
    HAS_STEALTH = False
    class Stealth:
        def apply_stealth_sync(self, page):
            pass

from scrapers.base_scraper import BaseScraper, JobListing


class ITGiantsScraper(BaseScraper):
    """Scraper tailored for major Indian IT Services companies restricted to India."""

    @property
    def source_name(self) -> str:
        return "IT_Giants"

    def _is_india_location(self, loc: str) -> bool:
        if not loc:
            return False
        loc_lower = loc.lower()
        indian_keywords = {
            "india", "bangalore", "bengaluru", "hyderabad", "pune", "mumbai", 
            "delhi", "noida", "gurgaon", "gurugram", "chennai", "kolkata", 
            "ahmedabad", "jaipur", "chandigarh", "kochi", "thiruvananthapuram", "mysore", "trivandrum"
        }
        return any(k in loc_lower for k in indian_keywords)

    def scrape(self, keywords: str, location: str, max_pages: int = 1) -> List[JobListing]:
        jobs = []
        
        print(f"  [ITGiants] Starting dedicated search for '{keywords}' in India...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=self._get_headers()["User-Agent"])

            # 1. TCS
            try:
                jobs.extend(self._scrape_tcs(context, keywords))
            except Exception as e:
                print(f"  [ITGiants - TCS] Error: {e}")

            # 2. Infosys
            try:
                jobs.extend(self._scrape_infosys(context, keywords))
            except Exception as e:
                print(f"  [ITGiants - Infosys] Error: {e}")

            # 3. Wipro
            try:
                jobs.extend(self._scrape_wipro(context, keywords))
            except Exception as e:
                print(f"  [ITGiants - Wipro] Error: {e}")

            # 4. Accenture
            try:
                jobs.extend(self._scrape_accenture(context, keywords))
            except Exception as e:
                print(f"  [ITGiants - Accenture] Error: {e}")

            # 5. Capgemini
            try:
                jobs.extend(self._scrape_capgemini(context, keywords))
            except Exception as e:
                print(f"  [ITGiants - Capgemini] Error: {e}")

            # 6. HCLTech
            try:
                jobs.extend(self._scrape_hcl(context, keywords))
            except Exception as e:
                print(f"  [ITGiants - HCLTech] Error: {e}")

            # 7. IBM
            try:
                jobs.extend(self._scrape_ibm(context, keywords))
            except Exception as e:
                print(f"  [ITGiants - IBM] Error: {e}")

            # 8. Tech Mahindra
            try:
                jobs.extend(self._scrape_techmahindra(context, keywords))
            except Exception as e:
                print(f"  [ITGiants - Tech Mahindra] Error: {e}")

            browser.close()

        print(f"  [ITGiants] Completed. Found {len(jobs)} jobs in India across top IT companies.")
        return jobs


    def _scrape_tcs(self, context, keywords: str) -> List[JobListing]:
        jobs = []
        page = context.new_page()
        Stealth().apply_stealth_sync(page)
        search_kw = quote_plus(keywords)
        url = f"https://ibegin.tcs.com/iBegin/jobs/search?Skill={search_kw}"
        
        print(f"  [ITGiants - TCS] Searching: {url}")
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(5000)
            page.wait_for_selector(".job-card, .list-group-item, .card", timeout=15000)
        except:
            print(f"  [ITGiants - TCS] No job cards found or timed out.")
            page.close()
            return jobs

        time.sleep(3)
        html = page.content()
        soup = BeautifulSoup(html, "lxml")
        
        job_elements = soup.select(".job-card, .list-group-item")
        for elem in job_elements:
            title_el = elem.select_one("h3 a, a.job-title, h4")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            job_url = title_el.get("href", "")
            if job_url and not job_url.startswith("http"):
                job_url = "https://ibegin.tcs.com" + job_url
                
            loc_el = elem.select_one(".location, .fa-map-marker + span, .job-location")
            job_loc = loc_el.get_text(strip=True) if loc_el else "India"
            
            if self._is_india_location(job_loc) or "india" in title.lower():
                jobs.append(JobListing(title=title[:200], company="TCS", location=job_loc, description="", url=job_url, source=self.source_name))
        
        page.close()
        print(f"  [ITGiants - TCS] Found {len(jobs)} jobs.")
        return jobs

    def _scrape_infosys(self, context, keywords: str) -> List[JobListing]:
        jobs = []
        page = context.new_page()
        Stealth().apply_stealth_sync(page)
        search_kw = quote_plus(keywords)
        url = f"https://career.infosys.com/joblist?keyword={search_kw}&location=India"
        
        print(f"  [ITGiants - Infosys] Searching: {url}")
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(5000)
            page.wait_for_selector(".job-details, .card, tr.job-row", timeout=15000)
        except:
            print(f"  [ITGiants - Infosys] No job cards found or timed out.")
            page.close()
            return jobs

        time.sleep(3)
        html = page.content()
        soup = BeautifulSoup(html, "lxml")
        
        job_elements = soup.select(".job-details, .card, tr.job-row")
        for elem in job_elements:
            title_el = elem.select_one("h3 a, a.job-title, .title a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            job_url = title_el.get("href", "")
            if job_url and not job_url.startswith("http"):
                job_url = "https://career.infosys.com" + job_url
                
            loc_el = elem.select_one(".location, .job-location")
            job_loc = loc_el.get_text(strip=True) if loc_el else "India"
            
            if self._is_india_location(job_loc):
                jobs.append(JobListing(title=title[:200], company="Infosys", location=job_loc, description="", url=job_url, source=self.source_name))
        
        page.close()
        print(f"  [ITGiants - Infosys] Found {len(jobs)} jobs.")
        return jobs

    def _scrape_wipro(self, context, keywords: str) -> List[JobListing]:
        jobs = []
        page = context.new_page()
        Stealth().apply_stealth_sync(page)
        search_kw = quote_plus(keywords)
        url = f"https://careers.wipro.com/careers-home/jobs?keywords={search_kw}&location=India"
        
        print(f"  [ITGiants - Wipro] Searching: {url}")
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(5000)
            page.wait_for_selector(".job-wrap, .mat-card, .job-item", timeout=15000)
        except:
            print(f"  [ITGiants - Wipro] No job cards found or timed out.")
            page.close()
            return jobs

        time.sleep(3)
        html = page.content()
        soup = BeautifulSoup(html, "lxml")
        
        job_elements = soup.select(".job-wrap, .mat-card, .job-item")
        for elem in job_elements:
            title_el = elem.select_one("a.job-title, h3 a, h2.title")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            job_url = title_el.get("href", "")
            if job_url and not job_url.startswith("http"):
                job_url = "https://careers.wipro.com" + job_url
                
            loc_el = elem.select_one(".location, .job-info-location")
            job_loc = loc_el.get_text(strip=True) if loc_el else "India"
            
            if self._is_india_location(job_loc):
                jobs.append(JobListing(title=title[:200], company="Wipro", location=job_loc, description="", url=job_url, source=self.source_name))
        
        page.close()
        print(f"  [ITGiants - Wipro] Found {len(jobs)} jobs.")
        return jobs

    def _scrape_accenture(self, context, keywords: str) -> List[JobListing]:
        jobs = []
        page = context.new_page()
        Stealth().apply_stealth_sync(page)
        search_kw = quote_plus(keywords)
        url = f"https://www.accenture.com/in-en/careers/jobsearch?jk={search_kw}"
        
        print(f"  [ITGiants - Accenture] Searching: {url}")
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(5000)
            page.wait_for_selector(".job-card, .card-job, .cmp-tej-job-card", timeout=15000)
        except:
            print(f"  [ITGiants - Accenture] No job cards found or timed out.")
            page.close()
            return jobs

        time.sleep(3)
        html = page.content()
        soup = BeautifulSoup(html, "lxml")
        
        job_elements = soup.select(".job-card, .card-job, .cmp-tej-job-card")
        for elem in job_elements:
            title_el = elem.select_one(".job-title a, h3 a, a.job-card-title")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            job_url = title_el.get("href", "")
            if job_url and not job_url.startswith("http"):
                job_url = "https://www.accenture.com" + job_url
                
            loc_el = elem.select_one(".job-location, span.location")
            job_loc = loc_el.get_text(strip=True) if loc_el else "India"
            
            if self._is_india_location(job_loc) or "india" in title.lower():
                jobs.append(JobListing(title=title[:200], company="Accenture", location=job_loc, description="", url=job_url, source=self.source_name))
        
        page.close()
        print(f"  [ITGiants - Accenture] Found {len(jobs)} jobs.")
        return jobs

    def _scrape_capgemini(self, context, keywords: str) -> List[JobListing]:
        jobs = []
        page = context.new_page()
        Stealth().apply_stealth_sync(page)
        search_kw = quote_plus(keywords)
        url = f"https://www.capgemini.com/in-en/careers/jobs/?search_keyword={search_kw}"
        
        print(f"  [ITGiants - Capgemini] Searching: {url}")
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(5000)
            page.wait_for_selector(".job_listing, .card-job", timeout=15000)
        except:
            print(f"  [ITGiants - Capgemini] No job cards found or timed out.")
            page.close()
            return jobs

        time.sleep(3)
        html = page.content()
        soup = BeautifulSoup(html, "lxml")
        
        job_elements = soup.select(".job_listing, .card-job")
        for elem in job_elements:
            title_el = elem.select_one(".job_listing-title a, h3 a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            job_url = title_el.get("href", "")
            if job_url and not job_url.startswith("http"):
                job_url = "https://www.capgemini.com" + job_url
                
            loc_el = elem.select_one(".location, .job_listing-location")
            job_loc = loc_el.get_text(strip=True) if loc_el else "India"
            
            if self._is_india_location(job_loc):
                jobs.append(JobListing(title=title[:200], company="Capgemini", location=job_loc, description="", url=job_url, source=self.source_name))
        
        page.close()
        print(f"  [ITGiants - Capgemini] Found {len(jobs)} jobs.")
        return jobs

    def _scrape_hcl(self, context, keywords: str) -> List[JobListing]:
        jobs = []
        page = context.new_page()
        Stealth().apply_stealth_sync(page)
        search_kw = quote_plus(keywords)
        url = f"https://www.hcltech.com/careers/explore-jobs?search_keyword={search_kw}"
        
        print(f"  [ITGiants - HCLTech] Searching: {url}")
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(5000)
            page.wait_for_selector(".views-row, .job-row, .node--type-job", timeout=15000)
        except:
            print(f"  [ITGiants - HCLTech] No job cards found or timed out.")
            page.close()
            return jobs

        time.sleep(3)
        html = page.content()
        soup = BeautifulSoup(html, "lxml")
        
        job_elements = soup.select(".views-row, .job-row, .node--type-job")
        for elem in job_elements:
            title_el = elem.select_one(".views-field-title a, h2 a, a.job-title")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            job_url = title_el.get("href", "")
            if job_url and not job_url.startswith("http"):
                job_url = "https://www.hcltech.com" + job_url
                
            loc_el = elem.select_one(".views-field-field-job-location, .location")
            job_loc = loc_el.get_text(strip=True) if loc_el else "India"
            
            if self._is_india_location(job_loc):
                jobs.append(JobListing(title=title[:200], company="HCLTech", location=job_loc, description="", url=job_url, source=self.source_name))
        
        page.close()
        print(f"  [ITGiants - HCLTech] Found {len(jobs)} jobs.")
        return jobs

    def _scrape_ibm(self, context, keywords: str) -> List[JobListing]:
        jobs = []
        page = context.new_page()
        Stealth().apply_stealth_sync(page)
        search_kw = quote_plus(keywords)
        url = f"https://careers.ibm.com/job/search/?keyword={search_kw}&location=India"
        
        print(f"  [ITGiants - IBM] Searching: {url}")
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(5000)
            page.wait_for_selector(".job-card, .job-row, .bx--card", timeout=15000)
        except:
            print(f"  [ITGiants - IBM] No job cards found or timed out.")
            page.close()
            return jobs

        time.sleep(3)
        html = page.content()
        soup = BeautifulSoup(html, "lxml")
        
        job_elements = soup.select(".job-card, .job-row, .bx--card")
        for elem in job_elements:
            title_el = elem.select_one(".job-title a, h3 a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            job_url = title_el.get("href", "")
            if job_url and not job_url.startswith("http"):
                job_url = "https://careers.ibm.com" + job_url
                
            loc_el = elem.select_one(".location, .bx--card__footer")
            job_loc = loc_el.get_text(strip=True) if loc_el else "India"
            
            if self._is_india_location(job_loc):
                jobs.append(JobListing(title=title[:200], company="IBM", location=job_loc, description="", url=job_url, source=self.source_name))
        
        page.close()
        print(f"  [ITGiants - IBM] Found {len(jobs)} jobs.")
        return jobs

    def _scrape_techmahindra(self, context, keywords: str) -> List[JobListing]:
        jobs = []
        page = context.new_page()
        Stealth().apply_stealth_sync(page)
        search_kw = quote_plus(keywords)
        url = f"https://careers.techmahindra.com/job-search.aspx?keywords={search_kw}"
        
        print(f"  [ITGiants - Tech Mahindra] Searching: {url}")
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(5000)
            page.wait_for_selector(".job-list, .job-item, .card", timeout=15000)
        except:
            print(f"  [ITGiants - Tech Mahindra] No job cards found or timed out.")
            page.close()
            return jobs

        time.sleep(3)
        html = page.content()
        soup = BeautifulSoup(html, "lxml")
        
        job_elements = soup.select(".job-list, .job-item, .card")
        for elem in job_elements:
            title_el = elem.select_one(".job-title a, h3 a, h2 a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            job_url = title_el.get("href", "")
            if job_url and not job_url.startswith("http"):
                job_url = "https://careers.techmahindra.com" + job_url
                
            loc_el = elem.select_one(".location, .job-loc")
            job_loc = loc_el.get_text(strip=True) if loc_el else "India"
            
            if self._is_india_location(job_loc):
                jobs.append(JobListing(title=title[:200], company="Tech Mahindra", location=job_loc, description="", url=job_url, source=self.source_name))
        
        page.close()
        print(f"  [ITGiants - Tech Mahindra] Found {len(jobs)} jobs.")
        return jobs
