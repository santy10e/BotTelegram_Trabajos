"""Multitrabajos es una SPA: las ofertas se obtienen de su API JSON pública de búsqueda."""
from __future__ import annotations

from ..models import Job
from .base import normalize, request_json, slugify

NAME = "Multitrabajos"
BASE_URL = "https://www.multitrabajos.com"
SITE_ID = "BMEC"  # Bumeran Ecuador
PAGE_SIZE = 50


def fetch(query: str, city: str) -> list[Job]:
    data = request_json(
        "POST",
        f"{BASE_URL}/api/avisos/searchV2",
        params={"pageSize": PAGE_SIZE, "page": 0, "sort": "RECIENTES"},
        headers={"x-site-id": SITE_ID, "Referer": f"{BASE_URL}/"},
        json={"filtros": [], "query": query, "internacional": False},
    )

    wanted_city = normalize(city)
    jobs: list[Job] = []
    for item in data.get("content", []):
        location = item.get("localizacion") or ""
        if wanted_city not in normalize(location):
            continue
        title = item.get("titulo") or ""
        company = item.get("empresa") or ""
        slug = "-".join(filter(None, (slugify(title), slugify(company), str(item.get("id", "")))))
        job = Job.build(
            title=title,
            link=f"{BASE_URL}/empleos/{slug}.html" if item.get("id") else None,
            company=None if item.get("confidencial") else company,
            location=location,
            source=NAME,
        )
        if job:
            jobs.append(job)
    return jobs
