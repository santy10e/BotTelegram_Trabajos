"""
import requests

def fetch():
    r = requests.get("https://remoteok.com/api")
    jobs = []
    for j in r.json()[1:]:
        jobs.append({
            "title": j["position"],
            "company": j["company"],
            "location": "Remoto",
            "link": j["url"],
            "source": "RemoteOK"
        })
    return jobs
    """