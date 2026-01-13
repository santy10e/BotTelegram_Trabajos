import requests
from bs4 import BeautifulSoup

def fetch():
    url = "https://ec.indeed.com/jobs?q=desarrollador&l=Quito"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")

    jobs = []
    for o in soup.select(".job_seen_beacon"):
        try:
            jobs.append({
                "title": o.select_one("h2 span").text,
                "company": o.select_one(".companyName").text,
                "location": o.select_one(".companyLocation").text,
                "link": "https://ec.indeed.com" + o.select_one("a")["href"],
                "source": "Indeed"
            })
        except:
            continue
    return jobs