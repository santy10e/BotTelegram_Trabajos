import requests

def fetch():
    urls = [
        "https://www.google.com/search?q=site:linkedin.com/jobs+desarrollador+Quito",
        "https://www.google.com/search?q=site:glassdoor.com+software+Quito"
    ]

    jobs = []
    for url in urls:
        jobs.append({
            "title": "Ver resultados indexados",
            "company": "Multiple",
            "location": "Quito",
            "link": url,
            "source": "Indexador"
        })
    return jobs