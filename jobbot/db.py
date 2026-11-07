"""Persistencia en SQLite: ofertas vistas y suscriptores."""
from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .models import Job

_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT,
    company     TEXT,
    location    TEXT,
    link        TEXT UNIQUE,
    source      TEXT,
    created_at  TEXT
);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs (created_at);

CREATE TABLE IF NOT EXISTS subscribers (
    chat_id     INTEGER PRIMARY KEY,
    created_at  TEXT
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            with conn:  # commit / rollback automático
                yield conn
        finally:
            conn.close()

    def init(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    # ---------- Ofertas ----------
    def save_job_if_new(self, job: Job) -> bool:
        """Guarda la oferta; devuelve True solo si no existía."""
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT OR IGNORE INTO jobs (title, company, location, link, source, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (job.title, job.company, job.location, job.link, job.source, _now()),
            )
            return cur.rowcount == 1

    def count_jobs(self) -> int:
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]

    def latest_jobs(self, limit: int) -> list[Job]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT title, company, location, link, source FROM jobs "
                "ORDER BY created_at DESC, id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [Job(**dict(row)) for row in rows]

    # ---------- Suscriptores ----------
    def add_subscriber(self, chat_id: int) -> bool:
        """Devuelve True si es una suscripción nueva."""
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT OR IGNORE INTO subscribers (chat_id, created_at) VALUES (?, ?)",
                (chat_id, _now()),
            )
            return cur.rowcount == 1

    def remove_subscriber(self, chat_id: int) -> bool:
        """Devuelve True si el chat estaba suscrito."""
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM subscribers WHERE chat_id = ?", (chat_id,))
            return cur.rowcount == 1

    def is_subscribed(self, chat_id: int) -> bool:
        with self._connect() as conn:
            row = conn.execute("SELECT 1 FROM subscribers WHERE chat_id = ?", (chat_id,)).fetchone()
            return row is not None

    def subscribers(self) -> list[int]:
        with self._connect() as conn:
            return [row[0] for row in conn.execute("SELECT chat_id FROM subscribers")]

    def count_subscribers(self) -> int:
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM subscribers").fetchone()[0]
