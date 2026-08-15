import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote

def test_ddg():
    url = "https://html.duckduckgo.com/html/"
    params = {
        'q': 'site:careers.cognizant.com "java developer" India career OR jobs'
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    resp = requests.post(url, data=params, headers=headers)
    with open("ddg.html", "w", encoding="utf-8") as f:
        f.write(resp.text)
    
if __name__ == "__main__":
    test_ddg()
