import os
import sys

# Add the project root to the sys.path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from scrapers.cognizant_scraper import CognizantScraper

def test_cognizant():
    scraper = CognizantScraper()
    jobs = scraper.scrape("java backend developer", "India", 1)
    
    print(f"\nTotal Found: {len(jobs)} jobs")
    for j in jobs[:5]:
        print(f"- {j.title[:50]} | {j.location} | {j.url}")

if __name__ == "__main__":
    test_cognizant()
