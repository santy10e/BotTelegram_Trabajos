"""Empleos remotos globales de Remote OK.

Sus términos de uso piden citar "Remote OK" como fuente y enlazar a su web,
lo cual se cumple porque cada aviso muestra la fuente y el link original.
La ciudad se ignora: todas las ofertas son remotas. Conviene usar KEYWORDS.
"""
from __future__ import annotations

from ..models import Job
from .base import request_json

NAME = "Remote OK"
API_URL = "https://remoteok.com/api"


def fetch(query: str, city: str) -> list[Job]:
    data = request_json("GET", API_URL)
    jobs: list[Job] = []
    for item in data[1:]:  # el primer elemento es el aviso legal de la API
        job = Job.build(
            title=item.get("position"),
            link=item.get("url"),
            company=item.get("company"),
            location=f"Remoto · {item['location']}" if item.get("location") else "Remoto",
            source=NAME,
        )
        if job:
            jobs.append(job)
    return jobs
