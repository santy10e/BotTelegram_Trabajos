import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}

def fetch():
    url = "https://ec.computrabajo.com/trabajo-de-desarrollador-en-quito"
    r = requests.get(url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")

    jobs = []
    for o in soup.select(".box_offer"):
        try:
            jobs.append({
                "title": o.select_one("h2").text.strip(),
                "company": o.select_one(".company").text.strip(),
                "location": o.select_one(".location").text.strip(),
                "link": "https://ec.computrabajo.com" + o.select_one("a")["href"],
                "source": "Computrabajo"
            })
        except:
            continue
    return jobs