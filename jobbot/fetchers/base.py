"""Utilidades HTTP/HTML compartidas por los fetchers."""
from __future__ import annotations

import re
import unicodedata
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag

TIMEOUT_SECONDS = 20
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "es-EC,es;q=0.9,en;q=0.8",
}


def get_soup(url: str, **kwargs: Any) -> BeautifulSoup:
    response = requests.get(url, headers=HEADERS, timeout=TIMEOUT_SECONDS, **kwargs)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def request_json(method: str, url: str, *, headers: dict[str, str] | None = None, **kwargs: Any) -> Any:
    response = requests.request(
        method, url, headers={**HEADERS, **(headers or {})}, timeout=TIMEOUT_SECONDS, **kwargs
    )
    response.raise_for_status()
    return response.json()


def text_of(node: Tag, selector: str) -> str:
    el = node.select_one(selector)
    return el.get_text(" ", strip=True) if el else ""


def normalize(text: str) -> str:
    """Minúsculas y sin tildes, para comparar texto."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower()


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", normalize(text)).strip("-")
