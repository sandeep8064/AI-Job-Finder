import requests
import json

def test_pwc():
    print("Testing PwC...")
    r = requests.post(
        "https://pwc.wd3.myworkdayjobs.com/wday/cxs/pwc/Global_Experienced_Careers/jobs",
        json={"appliedFacets":{},"limit":20,"offset":0,"searchText":"java"},
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)","Accept": "application/json","Content-Type": "application/json"}
    )
    if r.status_code == 200:
        data = r.json()
        print(f"PwC OK: {len(data.get('jobPostings', []))} jobs")
    else:
        print(f"PwC Failed: {r.status_code}")

def test_deloitte():
    print("\nTesting Deloitte...")
    urls = [
        "https://apply.deloitte.com/api/apply/v2/jobs?domain=deloitte.com&start=0&num=10&query=java",
        "https://apply.deloitte.com/api/apply/v3/jobs?domain=deloitte.com&start=0&num=10&query=java",
        "https://apply.deloitte.com/careers/api/apply/v2/jobs?domain=deloitte.com&start=0&num=10&query=java"
    ]
    for url in urls:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        print(f"Deloitte {url} -> {r.status_code}")

def test_kpmg():
    print("\nTesting KPMG (Avature)...")
    url = "https://kpmgindia.avature.net/careers/SearchJobs/?keyword=java"
    # Avature usually responds with a custom JSON when X-Requested-With header is set
    r = requests.get(url, headers={
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest"
    })
    print(f"KPMG Status: {r.status_code}, length: {len(r.text)}")

test_pwc()
test_deloitte()
test_kpmg()
