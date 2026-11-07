"""Configuración central.

Todo valor sensible (token, chat_id de administradores) se lee del entorno o
del archivo `.env`; nunca debe escribirse en el código.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

MIN_INTERVAL_SECONDS = 300


class ConfigError(RuntimeError):
    """Configuración inválida o incompleta."""


@dataclass(frozen=True)
class Settings:
    telegram_token: str
    admin_chat_ids: frozenset[int]
    search_query: str
    search_city: str
    sources: tuple[str, ...]
    keywords: tuple[str, ...]
    exclude_keywords: tuple[str, ...]
    check_interval: int
    db_path: Path
    log_level: str


def _csv(name: str, default: str = "") -> tuple[str, ...]:
    raw = os.getenv(name, default)
    return tuple(item.strip() for item in raw.split(",") if item.strip())


def _int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} debe ser un número entero (valor actual: {raw!r}).") from exc


def load_settings() -> Settings:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise ConfigError(
            "Falta TELEGRAM_BOT_TOKEN. Copia .env.example como .env y coloca el token de @BotFather."
        )

    admins: set[int] = set()
    for raw in _csv("ADMIN_CHAT_IDS"):
        try:
            admins.add(int(raw))
        except ValueError as exc:
            raise ConfigError(f"ADMIN_CHAT_IDS contiene un valor inválido: {raw!r}.") from exc

    interval = _int("CHECK_INTERVAL_SECONDS", 1800)
    if interval < MIN_INTERVAL_SECONDS:
        raise ConfigError(
            f"CHECK_INTERVAL_SECONDS debe ser al menos {MIN_INTERVAL_SECONDS} para no saturar los portales."
        )

    db_path = Path(os.getenv("DB_PATH", "").strip() or "jobs.db")
    if not db_path.is_absolute():
        db_path = BASE_DIR / db_path

    return Settings(
        telegram_token=token,
        admin_chat_ids=frozenset(admins),
        search_query=os.getenv("SEARCH_QUERY", "desarrollador").strip() or "desarrollador",
        search_city=os.getenv("SEARCH_CITY", "quito").strip() or "quito",
        sources=tuple(s.lower() for s in _csv("SOURCES", "computrabajo,multitrabajos")),
        keywords=_csv("KEYWORDS"),
        exclude_keywords=_csv("EXCLUDE_KEYWORDS"),
        check_interval=interval,
        db_path=db_path,
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO",
    )
