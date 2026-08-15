"""
Base scraper — Abstract class for all job scrapers.
Provides common utilities: rate limiting, user-agent rotation, retry logic.
"""
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@dataclass
class JobListing:
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str  # "naukri", "linkedin", "career_page"
    posted_date: Optional[str] = None
    experience: Optional[str] = None
    skills: List[str] = field(default_factory=list)

    @property
    def unique_id(self) -> str:
        """Generate a unique identifier for deduplication."""
        import hashlib
        key = f"{self.title}|{self.company}|{self.url}".lower().strip()
        return hashlib.md5(key.encode()).hexdigest()


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
]


class BaseScraper(ABC):
    """Abstract base class for all job scrapers."""

    def __init__(self, rate_limit: float = 2.0):
        self.rate_limit = rate_limit
        self._last_request_time = 0.0
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _get_headers(self) -> dict:
        """Get request headers with a random user agent."""
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

    def _rate_limit_wait(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit:
            sleep_time = self.rate_limit - elapsed + random.uniform(0.5, 1.5)
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    def _fetch(self, url: str, params: dict = None) -> Optional[str]:
        """Fetch a URL with rate limiting, retries, and user-agent rotation."""
        self._rate_limit_wait()
        try:
            response = self.session.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=15,
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"  [!] Error fetching {url}: {e}")
            return None

    @abstractmethod
    def scrape(self, keywords: str, location: str, max_pages: int = 3) -> List[JobListing]:
        """
        Scrape jobs matching the given criteria.

        Args:
            keywords: Job search keywords (e.g. "python developer")
            location: Location filter (e.g. "Bangalore")
            max_pages: Maximum pages to scrape

        Returns:
            List of JobListing objects
        """
        pass

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name of this scraper source (e.g. 'naukri', 'linkedin')."""
        pass
