import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

print("Starting driver...")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})

try:
    print("Navigating to Naukri...")
    driver.get("https://www.naukri.com/python-jobs-in-india")
    time.sleep(5) # wait for React
    soup = BeautifulSoup(driver.page_source, "lxml")
    cards = soup.select("article.jobTuple, .srp-jobtuple-wrapper, .jobTuple")
    print(f"Cards found: {len(cards)}")
    if cards:
        print(cards[0].get_text(separator=' | ')[:100])
finally:
    driver.quit()
