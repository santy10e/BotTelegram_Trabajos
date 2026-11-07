"""Indeed suele responder 403 (protección anti-bots); por eso está desactivado por defecto."""
from __future__ import annotations

from urllib.parse import urljoin

from ..models import Job
from .base import get_soup, text_of

NAME = "Indeed"
BASE_URL = "https://ec.indeed.com"


def fetch(query: str, city: str) -> list[Job]:
    soup = get_soup(f"{BASE_URL}/jobs", params={"q": query, "l": city, "sort": "date"})

    jobs: list[Job] = []
    for offer in soup.select(".job_seen_beacon"):
        anchor = offer.select_one("h2 a[href]")
        if anchor is None:
            continue
        job = Job.build(
            title=text_of(offer, "h2 span") or anchor.get_text(strip=True),
            link=urljoin(BASE_URL, anchor["href"]),
            company=text_of(offer, "[data-testid='company-name']") or text_of(offer, ".companyName"),
            location=text_of(offer, "[data-testid='text-location']") or text_of(offer, ".companyLocation"),
            source=NAME,
        )
        if job:
            jobs.append(job)
    return jobs
