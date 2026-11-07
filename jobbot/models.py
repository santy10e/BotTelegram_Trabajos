from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urldefrag

DEFAULT_COMPANY = "Empresa confidencial"
DEFAULT_LOCATION = "No especificada"


def _clean(value: str | None) -> str:
    return " ".join((value or "").split())


@dataclass(frozen=True, slots=True)
class Job:
    title: str
    company: str
    location: str
    link: str
    source: str

    @classmethod
    def build(
        cls,
        *,
        title: str | None,
        link: str | None,
        source: str,
        company: str | None = None,
        location: str | None = None,
    ) -> Job | None:
        """Normaliza los campos; devuelve None si falta título o un link http(s) válido."""
        title = _clean(title)
        link = urldefrag(_clean(link)).url  # quita "#tracking" para que el link sea estable
        if not title or not link.startswith(("http://", "https://")):
            return None
        return cls(
            title=title,
            company=_clean(company) or DEFAULT_COMPANY,
            location=_clean(location) or DEFAULT_LOCATION,
            link=link,
            source=source,
        )
