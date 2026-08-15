"""
Quick test for TinyFish scraper integration.
Tests API connectivity and job extraction.

Usage:
    Set TINYFISH_API_KEY env var or pass via --api-key flag.
    python test_tinyfish.py
    python test_tinyfish.py --api-key sk-tinyfish-...
"""
import argparse
import os
import sys

from scrapers.tinyfish_scraper import TinyFishScraper


def test_tinyfish(api_key: str):
    """Test TinyFish scraper with a single target URL."""
    print("=" * 60)
    print("  TinyFish Integration Test")
    print("=" * 60)

    if not api_key:
        print("\n✗ No API key provided.")
        print("  Set TINYFISH_API_KEY env var or use --api-key flag.")
        sys.exit(1)

    print(f"\n[1/3] API Key: {api_key[:12]}...{api_key[-4:]}")

    # Test with a single, reliable job site
    test_url = "https://in.indeed.com"
    test_keyword = "java developer"
    test_location = "India"

    print(f"\n[2/3] Testing extraction from: {test_url}")
    print(f"  Keywords: '{test_keyword}' | Location: '{test_location}'")

    scraper = TinyFishScraper(
        api_key=api_key,
        rate_limit=1.0,
        browser_profile="stealth",
    )

    jobs = scraper.scrape(
        keywords=test_keyword,
        location=test_location,
        target_urls=[test_url],
    )

    print(f"\n[3/3] Results:")
    if jobs:
        print(f"  ✓ Found {len(jobs)} jobs!")
        print(f"\n  Sample jobs:")
        for i, job in enumerate(jobs[:5], 1):
            print(f"    {i}. {job.title}")
            print(f"       Company: {job.company}")
            print(f"       Location: {job.location}")
            print(f"       URL: {job.url[:80]}...")
            print(f"       Source: {job.source}")
            if job.posted_date:
                print(f"       Posted: {job.posted_date}")
            print()

        # Verify JobListing structure
        first = jobs[0]
        assert first.source == "tinyfish", "Source should be 'tinyfish'"
        assert first.title, "Title should not be empty"
        assert first.url.startswith("http"), "URL should be absolute"
        print("  ✓ All assertions passed!")
    else:
        print("  ⚠ No jobs found. This could mean:")
        print("    - The site blocked the request")
        print("    - The search returned no results")
        print("    - TinyFish Agent couldn't extract data")
        print("    Check the error messages above for details.")

    print(f"\n{'=' * 60}")
    print(f"  Test complete!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test TinyFish scraper integration")
    parser.add_argument("--api-key", type=str, help="TinyFish API key")
    args = parser.parse_args()

    key = args.api_key or os.getenv("TINYFISH_API_KEY", "")
    test_tinyfish(key)
