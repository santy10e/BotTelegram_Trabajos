from __future__ import annotations

import logging
from urllib.parse import urljoin

from ..models import Job
from .base import get_soup, slugify, text_of

NAME = "Computrabajo"
BASE_URL = "https://ec.computrabajo.com"
log = logging.getLogger(__name__)


def fetch(query: str, city: str) -> list[Job]:
    soup = get_soup(f"{BASE_URL}/trabajo-de-{slugify(query)}-en-{slugify(city)}")

    jobs: list[Job] = []
    for offer in soup.select("article.box_offer"):
        anchor = offer.select_one("h2 a[href]")
        if anchor is None:
            log.debug("Oferta sin enlace, se omite")
            continue
        job = Job.build(
            title=anchor.get_text(strip=True),
            link=urljoin(BASE_URL, anchor["href"]),
            company=text_of(offer, "[offer-grid-article-company-url]") or text_of(offer, "h2 + p"),
            location=text_of(offer, "p span.mr10"),
            source=NAME,
        )
        if job:
            jobs.append(job)
    return jobs
