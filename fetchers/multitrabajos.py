import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}

def fetch():
    url = "https://www.multitrabajos.com/empleos-en-quito-desarrollador.html"
    r = requests.get(url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")

    jobs = []
    for o in soup.select("article"):
        try:
            jobs.append({
                "title": o.select_one("h2").text.strip(),
                "company": o.select_one(".company").text.strip(),
                "location": "Quito",
                "link": o.select_one("a")["href"],
                "source": "Multitrabajos"
            })
        except:
            continue
    return jobs