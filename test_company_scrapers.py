import sys
import os

from scrapers.big4_scraper import Big4Scraper
from scrapers.it_giants_scraper import ITGiantsScraper

def test_scrapers():
    keyword = "java"
    location = "India"
    
    print("=" * 50)
    print("Testing Big 4 Scraper...")
    big4 = Big4Scraper()
    big4_jobs = big4.scrape(keyword, location)
    print(f"\nBig 4 Jobs found: {len(big4_jobs)}")
    for j in big4_jobs[:3]:
        print(f" - [{j.company}] {j.title} | {j.location} | {j.url}")
        
    print("\n" + "=" * 50)
    print("Testing IT Giants Scraper...")
    it_giants = ITGiantsScraper()
    itg_jobs = it_giants.scrape(keyword, location)
    print(f"\nIT Giants Jobs found: {len(itg_jobs)}")
    for j in itg_jobs[:3]:
        print(f" - [{j.company}] {j.title} | {j.location} | {j.url}")

if __name__ == "__main__":
    test_scrapers()
