"""
TinyFish AI Search API scraper — Uses TinyFish Search API to extract job listings.
This is 100% free and has no credit limits.
"""
import time
import random
import concurrent.futures
from typing import List, Optional
from urllib.parse import urlparse

import httpx

from scrapers.base_scraper import BaseScraper, JobListing


class TinyFishScraper(BaseScraper):
    """Scrapes job listings from any website using TinyFish Search API."""

    SEARCH_API_URL = "https://api.search.tinyfish.ai"
    FETCH_API_URL = "https://api.fetch.tinyfish.ai"
    REQUEST_TIMEOUT = 30  # Search API is much faster than Agent API

    def __init__(
        self,
        api_key: str,
        rate_limit: float = 2.0,
        browser_profile: str = "stealth",
    ):
        super().__init__(rate_limit)
        self.api_key = api_key
        self._http_client = httpx.Client(timeout=self.REQUEST_TIMEOUT)

    @property
    def source_name(self) -> str:
        return "tinyfish_search"

    def _call_search(self, query: str) -> Optional[List[dict]]:
        """Make a synchronous call to TinyFish Search API."""
        headers = {
            "X-API-Key": self.api_key,
        }
        params = {"query": query}

        try:
            response = self._http_client.get(
                self.SEARCH_API_URL,
                headers=headers,
                params=params,
            )

            if response.status_code == 429:
                print("  [TinyFish] Rate limited. Waiting 10s before retry...")
                time.sleep(10)
                response = self._http_client.get(
                    self.SEARCH_API_URL,
                    headers=headers,
                    params=params,
                )

            if response.status_code == 401:
                print("  [TinyFish] ✗ Invalid API key. Check your TinyFish API key.")
                return None

            if response.status_code != 200:
                print(f"  [TinyFish] API error (HTTP {response.status_code}): {response.text[:200]}")
                return None

            data = response.json()
            # The search API usually returns {"results": [{"title": "...", "url": "...", "snippet": "..."}, ...]}
            return data.get("results", [])

        except httpx.TimeoutException:
            print(f"  [TinyFish] Timeout after {self.REQUEST_TIMEOUT}s for query: {query}")
            return None
        except httpx.HTTPError as e:
            print(f"  [TinyFish] HTTP error: {e}")
            return None
        except Exception as e:
            print(f"  [TinyFish] Unexpected error: {e}")
            return None

    def _fetch_job_description(self, url: str):
        """Fetch the full clean markdown description for a job URL."""
        headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}
        payload = {"urls": [url]}
        try:
            response = self._http_client.post(self.FETCH_API_URL, headers=headers, json=payload, timeout=60.0)
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                if results and len(results) > 0:
                    text = results[0].get("text", "")
                    if text:
                        return text
            print(f"  [TinyFish Fetch] Warning: Could not fetch {url} (HTTP {response.status_code})")
        except Exception as e:
            print(f"  [TinyFish Fetch] Error fetching {url}: {e}")
        return None

    def scrape(
        self,
        keywords: str,
        location: str,
        max_pages: int = 3,
        target_urls: List[str] = None,
    ) -> List[JobListing]:
        if not self.api_key:
            print("  [TinyFish] ✗ No API key configured. Skipping TinyFish scraping.")
            return []

        if not target_urls:
            print("  [TinyFish] No target URLs configured. Skipping.")
            return []

        all_jobs: List[JobListing] = []
        print(f"  [TinyFish] Scraping {len(target_urls)} sites concurrently for '{keywords}' in '{location}'...")

        def _process_url(url: str) -> List[JobListing]:
            domain = urlparse(url).netloc
            if not domain:
                return []
            
            # Extract base domain for better search engine indexing
            # e.g., careers.hcltech.com -> hcltech.com
            parts = domain.split('.')
            if len(parts) > 2 and parts[-2] not in ('co', 'com', 'ac', 'net', 'org'):
                search_domain = f"{parts[-2]}.{parts[-1]}"
            elif len(parts) > 3 and parts[-2] in ('co', 'com', 'ac', 'net', 'org'):
                search_domain = f"{parts[-3]}.{parts[-2]}.{parts[-1]}"
            else:
                search_domain = domain

            # Some specific overrides where the ATS domain differs from the company domain
            if "tcsapps.com" in search_domain: search_domain = "tcs.com"
            if "oraclecloud.com" in search_domain: search_domain = domain # Oracle ATS needs full subdomain

            # Clean up the company name for the email
            company = search_domain.split('.')[0].title()
            if "Wipro" in company: company = "Wipro"
            if "Infosys" in company: company = "Infosys"
            if "Tcs" in company: company = "TCS"
            if "Accenture" in company: company = "Accenture"
            if "Capgemini" in company: company = "Capgemini"

            # Targeted Search Dork
            # Targeted Search Dork with exclusions for articles and foreign locations
            exclusions = "-news -article -blog -usa -uk -romania -london -texas -tx -canada -australia -europe"
            query = f'site:{search_domain} "{keywords}" {location} (job OR jobs OR careers OR hiring) {exclusions}'
            print(f"  [TinyFish] 🔎 Querying: {query}")

            time.sleep(random.uniform(0.1, 1.0))
            self._rate_limit_wait()

            results = self._call_search(query)
            jobs = []
            if results:
                for res in results:
                    title = res.get("title", "")
                    link = res.get("url", "")
                    snippet = res.get("snippet", res.get("description", ""))
                    if not title or not link: continue

                    print(f"  [TinyFish] Fetching full description for: {title[:30]}...")
                    full_desc = self._fetch_job_description(link)
                    description = full_desc if full_desc else snippet

                    jobs.append(
                        JobListing(
                            title=title[:200],
                            company=company,
                            location=location,
                            description=description,
                            url=link,
                            source=self.source_name,
                            # Search API doesn't know exact dates natively
                            posted_date=None, 
                        )
                    )
                print(f"  [TinyFish] ✓ Found {len(jobs)} jobs from {domain}")
                return jobs
            else:
                print(f"  [TinyFish] ✗ No results from {domain}")
                return []

        # To respect the TinyFish free tier limit of 30 requests per minute,
        # we run sequentially with a strict 2.5s delay.
        MAX_WORKERS = 1
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_url = {executor.submit(_process_url, url): url for url in target_urls}

            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    jobs = future.result()
                    all_jobs.extend(jobs)
                    time.sleep(2.5)  # Enforce 30 requests per minute limit
                except Exception as exc:
                    print(f"  [TinyFish] ✗ Exception processing {url}: {exc}")

        print(f"  [TinyFish] Total: {len(all_jobs)} jobs extracted")
        return all_jobs

    def __del__(self):
        try:
            self._http_client.close()
        except:
            pass
