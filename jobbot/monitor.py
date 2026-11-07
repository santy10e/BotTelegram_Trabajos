"""Revisión periódica de portales y envío de avisos a los suscriptores."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

import requests
from telegram import Bot
from telegram.error import Forbidden, RetryAfter, TelegramError
from telegram.ext import ContextTypes

from . import messages
from .config import Settings
from .db import Database
from .fetchers import Source
from .fetchers.base import normalize
from .models import Job

log = logging.getLogger(__name__)

# Hasta este número de ofertas nuevas se envía una tarjeta por oferta; si hay más, un resumen.
MAX_INDIVIDUAL_CARDS = 3
# Pausa entre mensajes para respetar los límites de Telegram (~30 msg/s).
SEND_DELAY_SECONDS = 0.05


@dataclass
class SourceStatus:
    ok: bool
    found: int = 0
    error: str = ""


@dataclass
class MonitorState:
    last_run: datetime | None = None
    sources: dict[str, SourceStatus] = field(default_factory=dict)


def _describe_error(exc: Exception) -> str:
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        return f"bloqueado o sin respuesta (HTTP {exc.response.status_code})"
    if isinstance(exc, requests.Timeout):
        return "tiempo de espera agotado"
    if isinstance(exc, requests.ConnectionError):
        return "sin conexión"
    return f"error inesperado ({type(exc).__name__})"


class JobMonitor:
    def __init__(self, settings: Settings, db: Database, sources: list[Source]) -> None:
        self.settings = settings
        self.db = db
        self.sources = sources
        self.state = MonitorState()
        self._lock = asyncio.Lock()
        self._include = tuple(normalize(k) for k in settings.keywords)
        self._exclude = tuple(normalize(k) for k in settings.exclude_keywords)

    @property
    def running(self) -> bool:
        return self._lock.locked()

    def matches(self, job: Job) -> bool:
        title = normalize(job.title)
        if any(word in title for word in self._exclude):
            return False
        return not self._include or any(word in title for word in self._include)

    async def run(self, bot: Bot) -> int:
        """Ejecuta una revisión completa. Devuelve cuántas ofertas nuevas se encontraron."""
        if self._lock.locked():
            log.info("Ya hay una revisión en curso; se omite esta.")
            return 0
        async with self._lock:
            first_run = self.db.count_jobs() == 0
            jobs = await self._fetch_all()
            new_jobs = [job for job in jobs if self.matches(job) and self.db.save_job_if_new(job)]
            self.state.last_run = datetime.now(timezone.utc)

        if first_run:
            # Evita inundar a los usuarios con todo el histórico en el primer arranque.
            log.info("Primera ejecución: %d ofertas registradas sin notificar.", len(new_jobs))
        elif new_jobs:
            log.info("%d ofertas nuevas; notificando.", len(new_jobs))
            await self._broadcast(bot, new_jobs)
        else:
            log.info("Sin ofertas nuevas.")
        return len(new_jobs)

    async def _fetch_all(self) -> list[Job]:
        query, city = self.settings.search_query, self.settings.search_city
        results = await asyncio.gather(
            *(asyncio.to_thread(source.fetch, query, city) for source in self.sources),
            return_exceptions=True,
        )
        jobs: list[Job] = []
        for source, result in zip(self.sources, results):
            if isinstance(result, Exception):
                log.warning("%s falló: %r", source.name, result)
                self.state.sources[source.name] = SourceStatus(ok=False, error=_describe_error(result))
            else:
                log.info("%s: %d ofertas", source.name, len(result))
                self.state.sources[source.name] = SourceStatus(ok=True, found=len(result))
                jobs.extend(result)
        return jobs

    async def _broadcast(self, bot: Bot, jobs: list[Job]) -> None:
        if len(jobs) <= MAX_INDIVIDUAL_CARDS:
            payloads = [(messages.job_card(job), messages.job_keyboard(job)) for job in jobs]
        else:
            payloads = [(text, None) for text in messages.digest(jobs)]

        for chat_id in self.db.subscribers():
            for text, markup in payloads:
                if not await self._send(bot, chat_id, text, markup):
                    break  # el chat ya no es válido: no seguir enviando
                await asyncio.sleep(SEND_DELAY_SECONDS)

    async def _send(self, bot: Bot, chat_id: int, text: str, markup, retry: bool = True) -> bool:
        try:
            await bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)
            return True
        except Forbidden:
            log.info("El chat %s bloqueó el bot; se elimina de suscriptores.", chat_id)
            self.db.remove_subscriber(chat_id)
            return False
        except RetryAfter as exc:
            if not retry:
                return True
            delay = exc.retry_after  # int en PTB 21; timedelta en versiones posteriores
            await asyncio.sleep(delay.total_seconds() if hasattr(delay, "total_seconds") else delay)
            return await self._send(bot, chat_id, text, markup, retry=False)
        except TelegramError as exc:
            log.warning("No se pudo enviar a %s: %s", chat_id, exc)
            return True


async def scheduled_check(context: ContextTypes.DEFAULT_TYPE) -> None:
    monitor: JobMonitor = context.bot_data["monitor"]
    await monitor.run(context.bot)
