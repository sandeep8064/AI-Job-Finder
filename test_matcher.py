from cv_parser.parser import parse_cv
from scrapers.base_scraper import JobListing
from matcher.matcher import match_jobs

def test_matcher():
    print("Loading CV...")
    cv = parse_cv(r"C:\Users\chsan\PycharmProjects\job_agent\uploads\Resume.pdf")
    print(f"Extracted CV Experience: {cv.experience_years} years")

    test_jobs = [
        JobListing(
            title="Senior Java Backend Developer",
            company="TechCorp",
            location="India",
            url="http://example.com/1",
            description="We need a massive expert in Java and AWS.",
            skills=["java", "aws", "spring boot", "docker"],
            experience="5 - 8 Yrs",
            source="Test"
        ),
        JobListing(
            title="Java Backend Developer",
            company="PerfectFit Inc",
            location="India",
            url="http://example.com/2",
            description="Looking for an experienced backend developer.",
            skills=["java", "aws", "spring boot", "docker", "ci/cd"],
            experience="2-4 Yrs",
            source="Test"
        ),
        JobListing(
            title="Software Developer",
            company="Random Startup",
            location="India",
            url="http://example.com/3",
            description="Some coding needed.",
            skills=["python"],
            experience="0-1 Yrs",
            source="Test"
        )
    ]

    print("\nMatching Jobs...")
    scored = match_jobs(cv, test_jobs, threshold=0.0)
    
    print("\nResults:")
    for sj in scored:
        print(f"\n[Score: {sj.score_pct}%] {sj.job.title} at {sj.job.company}")
        print(f"  Exp Reqd: {sj.job.experience}")
        print(f"  Match Reasons:")
        for r in sj.match_reasons:
            print(f"   - {r}")

if __name__ == "__main__":
    test_matcher()
