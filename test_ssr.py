import requests
from bs4 import BeautifulSoup

def test_company(name, url, selector):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(r.text, 'lxml')
        items = soup.select(selector)
        print(f"[{name}] {r.status_code} - Found {len(items)} items using selector '{selector}'")
    except Exception as e:
        print(f"[{name}] Failed: {e}")

test_company("TCS", "https://ibegin.tcs.com/iBegin/jobs/search?Skill=java", ".job-card, .list-group-item")
test_company("Infosys", "https://career.infosys.com/joblist?keyword=java&location=India", ".job-details, tr.job-row")
test_company("Wipro", "https://careers.wipro.com/careers-home/jobs?keywords=java&location=India", ".job-wrap, .mat-card")
test_company("Accenture", "https://www.accenture.com/in-en/careers/jobsearch?jk=java", ".job-card, .cmp-tej-job-card")
test_company("Capgemini", "https://www.capgemini.com/in-en/careers/jobs/?search_keyword=java", ".job_listing, .card-job")
test_company("HCLTech", "https://www.hcltech.com/careers/explore-jobs?search_keyword=java", ".views-row, .node--type-job")
test_company("IBM", "https://careers.ibm.com/job/search/?keyword=java&location=India", ".job-card, .bx--card")
test_company("TechM", "https://careers.techmahindra.com/job-search.aspx?keywords=java", ".job-list, .job-item, .card")
