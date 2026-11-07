"""Registro de portales. Cada fetcher expone NAME y fetch(query, city) -> list[Job]."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from ..config import ConfigError
from ..models import Job
from . import computrabajo, indeed, multitrabajos, remoteok


@dataclass(frozen=True)
class Source:
    key: str
    name: str
    fetch: Callable[[str, str], list[Job]]


REGISTRY: dict[str, Source] = {
    key: Source(key, module.NAME, module.fetch)
    for key, module in {
        "computrabajo": computrabajo,
        "multitrabajos": multitrabajos,
        "indeed": indeed,
        "remoteok": remoteok,
    }.items()
}


def resolve(keys: tuple[str, ...]) -> list[Source]:
    unknown = [k for k in keys if k not in REGISTRY]
    if unknown:
        raise ConfigError(
            f"Portales desconocidos en SOURCES: {', '.join(unknown)}. "
            f"Disponibles: {', '.join(REGISTRY)}."
        )
    return [REGISTRY[k] for k in dict.fromkeys(keys)]
