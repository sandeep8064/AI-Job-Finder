"""
Ai Job finder - Main entry point.
CLI commands: run-once, schedule, web
"""
import argparse
import os
import sys
import time
from datetime import datetime

from utils.time_utils import get_ist_strftime

try:
    import schedule as schedule_lib
    HAS_SCHEDULE = True
except ImportError:
    HAS_SCHEDULE = False


from config import load_config, save_config, UPLOAD_DIR, DB_PATH
from cv_parser.parser import parse_cv
from scrapers.naukri_scraper import NaukriScraper
from scrapers.linkedin_scraper import LinkedInScraper
from scrapers.career_scraper import CareerPageScraper
from scrapers.tinyfish_scraper import TinyFishScraper
from matcher.matcher import match_jobs
from notifier.email_sender import send_job_digest
from storage.db import JobDatabase


def is_in_india(location: str) -> bool:
    """Check if a location string likely refers to India or an Indian city."""
    if not location:
        return True  # If no location provided, assume it might match (or be safe)
    
    loc_lower = location.lower()
    indian_keywords = {
        "india", "bangalore", "bengaluru", "hyderabad", "pune", "mumbai", 
        "delhi", "noida", "gurgaon", "gurugram", "chennai", "kolkata", 
        "ahmedabad", "jaipur", "chandigarh", "lucknow", "indore", "kochi",
        "thiruvananthapuram", "mysore", "coimbatore", "nagpur", "remote"
    }
    
    # Check for exact keyword matches or mentions
    for kw in indian_keywords:
        if kw in loc_lower:
            return True
            
    return False


import re

def is_foreign_job(job) -> bool:
    """Check if the job title or description clearly mentions a foreign location."""
    foreign_keywords = [
        "usa", "uk", "us", "united states", "united kingdom", "london", "texas", "tx", "austin", 
        "california", "ca", "new york", "ny", "romania", "bucharest", "canada", "toronto", 
        "singapore", "dubai", "uae", "australia", "sydney", "melbourne", "europe", "poland", 
        "germany", "berlin", "munich", "france", "paris", "ireland", "dublin", "philippines", 
        "manila", "malaysia", "kuala lumpur", "mexico", "brazil", "japan", "china", "vietnam", 
        "thailand", "indonesia", "jakarta", "amsterdam", "netherlands", "dutch", "spain", "italy",
        "sweden", "switzerland", "south africa", "new zealand", "atlanta", "chicago", "seattle",
        "boston", "san francisco", "dallas", "houston", "miami", "florida", "fl", "washington", "dc"
    ]
    
    text_to_search = (job.title + " " + str(job.location or "")).lower()
    
    for kw in foreign_keywords:
        # Use word boundaries so we don't match 'us' inside 'focus', or 'ca' inside 'can'
        if re.search(r'\b' + re.escape(kw) + r'\b', text_to_search):
            return True
            
    return False



def run_pipeline(config=None, dry_run=False):
    """
    Run the full job agent pipeline:
    1. Parse CV
    2. Scrape all sources
    3. Match jobs to profile
    4. Filter new jobs (dedup)
    5. Send email digest
    """
    if config is None:
        config = load_config()

    print("=" * 60)
    print(f"  Ai Job finder - Pipeline Run")
    print(f"  {get_ist_strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # ── Step 1: Parse CV ─────────────────────────────────────────────────
    cv_path = config.cv_path
    if not cv_path or not os.path.exists(cv_path):
        print("\n✗ No CV found. Please upload a CV through the web dashboard or set cv_path in config.json")
        return

    print(f"\n[1/5] Parsing CV: {cv_path}")
    try:
        profile = parse_cv(cv_path)
        print(f"  [*] Skills found: {', '.join(profile.skills[:10])}{'...' if len(profile.skills) > 10 else ''}")
        print(f"  [*] Experience: {profile.experience_years} years")
        print(f"  [*] Job titles: {', '.join(profile.job_titles[:5])}")
    except Exception as e:
        print(f"  [X] Failed to parse CV: {e}")
        return

    # Dynamically update search keywords based on Resume
    # Filter out generic titles like "backend developer", only keep specific ones (e.g., "java developer")
    specific_titles = [t for t in profile.job_titles if "java" in t.lower()]
    
    if specific_titles:
        config.search.keywords = specific_titles[:1]  # take the best specific title
    else:
        config.search.keywords = ["Java Developer"]  # fallback if none found in CV
        
    print(f"\n  [*] Resume Search: Using {config.search.keywords} as search keywords.")

    # ── Step 2: Scrape all sources ───────────────────────────────────────
    print(f"\n[2/5] Scraping job sites...")
    all_jobs = []
    scrapers_config = [
        ("Naukri", NaukriScraper(rate_limit=config.rate_limit_seconds, naukri_config=config.naukri)),
        ("LinkedIn", LinkedInScraper(rate_limit=config.rate_limit_seconds)),
    ]

    for name, scraper in scrapers_config:
        for keyword in config.search.keywords:
            for location in config.search.locations:
                try:
                    jobs = scraper.scrape(keyword, location, config.search.max_pages)
                    all_jobs.extend(jobs)
                except Exception as e:
                    print(f"  [X] {name} error for '{keyword}' in '{location}': {e}")

    # Career page scraper
    if config.search.career_page_urls:
        career_scraper = CareerPageScraper(rate_limit=config.rate_limit_seconds)
        for keyword in config.search.keywords:
            try:
                jobs = career_scraper.scrape(
                    keyword, "", career_urls=config.search.career_page_urls
                )
                all_jobs.extend(jobs)
            except Exception as e:
                print(f"  [X] Career page error: {e}")

    print(f"\n  Total jobs scraped (Naukri/LinkedIn/Career): {len(all_jobs)}")

    # TinyFish AI Agent scraper — for sites that block traditional scrapers
    if config.tinyfish.enabled and config.tinyfish.api_key:
        print(f"\n  [TinyFish] 🐟 Starting AI-powered scraping...")
        tinyfish_scraper = TinyFishScraper(
            api_key=config.tinyfish.api_key,
            rate_limit=config.rate_limit_seconds,
            browser_profile=config.tinyfish.browser_profile,
        )
        for keyword in config.search.keywords:
            for location in config.search.locations:
                try:
                    jobs = tinyfish_scraper.scrape(
                        keyword, location,
                        target_urls=config.tinyfish.target_urls,
                    )
                    all_jobs.extend(jobs)
                except Exception as e:
                    print(f"  [TinyFish] Error for '{keyword}' in '{location}': {e}")
        print(f"  [TinyFish] Total jobs after TinyFish: {len(all_jobs)}")
    elif config.tinyfish.enabled and not config.tinyfish.api_key:
        print(f"\n  [TinyFish] ⚠ TinyFish enabled but no API key set. Skipping.")

    # ── Step 2.5: Strict Location Filtering ────────────────────────────────
    if config.search.locations:
        print(f"  [Strict] Filtering for jobs strictly in: {', '.join(config.search.locations)}...")
        before_count = len(all_jobs)
        
        target_locs_lower = [l.lower() for l in config.search.locations]
        valid_fallback_locs = ["remote", "pan india", "anywhere", "india"]
        
        filtered_by_loc = []
        for j in all_jobs:
            if is_foreign_job(j):
                continue
                
            if not j.location:
                # If the scraper couldn't find a location, keep it so we don't drop good jobs
                filtered_by_loc.append(j)
                continue
                
            loc_lower = j.location.lower()
            
            # Check if any target location is explicitly mentioned
            if any(t_loc in loc_lower for t_loc in target_locs_lower):
                filtered_by_loc.append(j)
            # If "india" is in target locations, check if the job is in India using the broader helper
            elif "india" in target_locs_lower and is_in_india(j.location):
                filtered_by_loc.append(j)
            # Check if it's a generic remote/India role
            elif any(fb in loc_lower for fb in valid_fallback_locs) and "bangalore" not in loc_lower and "pune" not in loc_lower and "chennai" not in loc_lower and "hyderabad" not in loc_lower and "gurgaon" not in loc_lower:
                filtered_by_loc.append(j)
                
        all_jobs = filtered_by_loc
        after_count = len(all_jobs)
        if before_count != after_count:
            print(f"  [Strict] Removed {before_count - after_count} jobs outside target locations.")

    if not all_jobs:
        print("  No jobs found. Check your search keywords and network connection.")
        return

    # ── Step 2.6: Strict Date Filtering (Last 10 days, 2 days for Naukri) ───────────────────
    print("  [Strict] Filtering for recent jobs (last 10 days, 2 days for Naukri)...")
    from utils.time_utils import parse_relative_date_to_timestamp
    now_ts = datetime.now().timestamp()
    ten_days_ago = now_ts - (10 * 86400)
    two_days_ago = now_ts - (2 * 86400)
    
    before_count = len(all_jobs)
    filtered_jobs = []
    for j in all_jobs:
        ts = parse_relative_date_to_timestamp(j.posted_date or "")
        if j.source.lower() == "naukri":
            if ts >= two_days_ago:
                filtered_jobs.append(j)
        else:
            if ts >= ten_days_ago:
                filtered_jobs.append(j)
                
    all_jobs = filtered_jobs
    after_count = len(all_jobs)
    if before_count != after_count:
        print(f"  [Strict] Removed {before_count - after_count} outdated jobs.")

    if not all_jobs:
        print("  No recent jobs found after date filtering.")
        return

    # ── Step 3: Match jobs ───────────────────────────────────────────────
    print(f"\n[3/5] Matching jobs to your profile...")
    scored_jobs = match_jobs(profile, all_jobs, threshold=config.match_threshold)
    print(f"  [*] {len(scored_jobs)} jobs matched (threshold: {config.match_threshold})")

    if scored_jobs:
        print(f"\n  Top 5 matches:")
        for i, sj in enumerate(scored_jobs[:5], 1):
            print(f"    {i}. [{sj.score_pct}%] {sj.job.title} at {sj.job.company} ({sj.job.source})")

    # ── Step 4: Filter unnotified jobs ───────────────────────────────────
    print(f"\n[4/5] Filtering unnotified jobs...")
    db = JobDatabase(DB_PATH)
    unnotified_matches = []
    
    for sj in scored_jobs:
        # Add to DB if new
        if db.is_new_job(sj.job):
            db.add_job(sj.job, score=sj.score)
        
        # Check if it has been notified before
        if not db.was_notified(sj.job):
            unnotified_matches.append(sj)

    print(f"  [*] {len(unnotified_matches)} unnotified matches (out of {len(scored_jobs)} matches)")

    # ── Step 5: Send email ───────────────────────────────────────────────
    print(f"\n[5/5] Sending email digest...")
    email_jobs = []
    if not unnotified_matches:
        print("  No unnotified jobs match your profile at this time.")
    else:
        # User requested: First try to find same day posting, then previous postings. 
        from utils.time_utils import parse_relative_date_to_timestamp
        unnotified_matches.sort(
            key=lambda sj: (parse_relative_date_to_timestamp(sj.job.posted_date or ""), sj.score), 
            reverse=True
        )

        # Enforce maximum of 2 jobs per company
        filtered_unnotified = []
        company_counts = {}
        for sj in unnotified_matches:
            c_name = sj.job.company.strip().lower() if sj.job.company else "unknown"
            if company_counts.get(c_name, 0) < 2:
                filtered_unnotified.append(sj)
                company_counts[c_name] = company_counts.get(c_name, 0) + 1
        unnotified_matches = filtered_unnotified


        # Step 1: Identify "Blazing Fresh" (Today) jobs
        now_ts = datetime.now().timestamp()
        six_hours_ago = now_ts - (6 * 60 * 60)
        
        # We'll consider anything with a timestamp from today or very recent as "Fresh"
        def is_fresh(sj):
            ts = parse_relative_date_to_timestamp(sj.job.posted_date or "")
            # If it's missing date (Naukri default) or explicitly today/recent
            return ts >= (now_ts - 86400) # Past 24 hours

        fresh_matches = [sj for sj in unnotified_matches if is_fresh(sj)]
        older_matches = [sj for sj in unnotified_matches if not is_fresh(sj)]
        
        # Strategy:
        # 1. Take up to 30 fresh jobs (they are already sorted by date/score)
        # 2. If we have < 30 fresh ones, fill the remainder with older matches
        
        email_jobs = fresh_matches[:30]
        needed = 30 - len(email_jobs)
        if needed > 0:
            email_jobs.extend(older_matches[:needed])

        print(f"  [*] Selected {len([sj for sj in email_jobs if is_fresh(sj)])} same-day/fresh jobs.")
        
        # Give it one final sort chronologically just to be safe
        email_jobs.sort(key=lambda sj: (parse_relative_date_to_timestamp(sj.job.posted_date or ""), sj.score), reverse=True)
        
        if dry_run:
            print(f"  [DRY RUN] Skipping email. Would have sent {len(email_jobs)} jobs. Top 10:")
            for sj in email_jobs[:10]:
                print(f"    - [Date: {sj.job.posted_date or 'Recent'}] [{sj.score_pct}%] {sj.job.title} at {sj.job.company}")
            success = False
        else:
            success = send_job_digest(config.email, email_jobs, max_jobs=30)
        if success:
            for sj in email_jobs:
                db.mark_notified(sj.job)

    # Log the run
    db.log_scrape_run(
        jobs_found=len(all_jobs),
        jobs_new=len(unnotified_matches),
        jobs_notified=len(email_jobs) if not dry_run else 0,
    )

    print(f"\n{'=' * 60}")
    print(f"  Pipeline complete!")
    print(f"{'=' * 60}\n")


def run_scheduled(config=None):
    """Run the pipeline on a schedule."""
    if config is None:
        config = load_config()

    if not HAS_SCHEDULE:
        print("Error: 'schedule' library is not installed. Please install it to use scheduled mode.")
        return

    interval = config.scrape_interval_hours
    print(f"Starting scheduled mode - running every {interval} hour(s)")
    print("Press Ctrl+C to stop.\n")

    # Run immediately on start
    run_pipeline(config)

    # Schedule periodic runs
    schedule_lib.every(interval).hours.do(run_pipeline, config=config)

    try:
        while True:
            schedule_lib.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\nScheduler stopped.")


def run_web():
    """Start the Flask web dashboard."""
    from web.app import create_app
    app = create_app()
    print("\n[*] Ai Job finder Dashboard running at: http://localhost:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=True)


def main():
    parser = argparse.ArgumentParser(
        description="Ai Job finder - Automated job search & notification system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py run-once --cv resume.pdf                  Run once with a CV
  python main.py run-once --cv resume.pdf --dry-run        Run without sending email
  python main.py schedule                                   Run on schedule
  python main.py web                                        Start web dashboard
        """,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # run-once
    run_once_parser = subparsers.add_parser("run-once", help="Run the pipeline once")
    run_once_parser.add_argument("--cv", type=str, help="Path to CV file (.pdf, .docx, .txt)")
    run_once_parser.add_argument("--dry-run", action="store_true", help="Skip sending email")

    # schedule
    schedule_parser = subparsers.add_parser("schedule", help="Run pipeline on a schedule")
    schedule_parser.add_argument("--cv", type=str, help="Path to CV file")

    # web
    subparsers.add_parser("web", help="Start the web dashboard")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    config = load_config()

    if hasattr(args, "cv") and args.cv:
        config.cv_path = os.path.abspath(args.cv)
        save_config(config)

    if args.command == "run-once":
        run_pipeline(config, dry_run=getattr(args, "dry_run", False))
    elif args.command == "schedule":
        run_scheduled(config)
    elif args.command == "web":
        run_web()


if __name__ == "__main__":
    main()
