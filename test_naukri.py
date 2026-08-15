import cloudscraper, json, re
scraper = cloudscraper.create_scraper()
r = scraper.get('https://www.naukri.com/python-jobs-in-india')
print('Status:', r.status_code)
m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', r.text, flags=re.DOTALL)
if m:
    data = json.loads(m.group(1))
    try:
        jobs = data['props']['pageProps']['initialState']['jobSearch']['jobDetails']
        for j in jobs[:2]:
            print(j.get('title'), '|', getattr(j.get('companyName'), 'get', lambda x: '')('name', j.get('companyName', '')))
    except KeyError as e:
        print('KeyError:', e)
else:
    print('No NEXT_DATA found.')
