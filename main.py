"""Punto de entrada: un único proceso con el bot de Telegram y el monitor programado."""
from __future__ import annotations

import logging
import sys

from telegram import LinkPreviewOptions, Update
from telegram.constants import ParseMode
from telegram.ext import Application, ApplicationBuilder, Defaults

from jobbot import handlers
from jobbot.config import ConfigError, Settings, load_settings
from jobbot.db import Database
from jobbot.fetchers import resolve
from jobbot.monitor import JobMonitor, scheduled_check

FIRST_CHECK_DELAY_SECONDS = 5


def configure_logging(level: str) -> None:
    logging.basicConfig(
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        level=level,
    )
    # httpx registra cada URL de la API de Telegram, que incluye el token: silenciarlo.
    logging.getLogger("httpx").setLevel(logging.WARNING)


def build_application(settings: Settings) -> Application:
    db = Database(settings.db_path)
    db.init()
    monitor = JobMonitor(settings, db, resolve(settings.sources))

    app = (
        ApplicationBuilder()
        .token(settings.telegram_token)
        .defaults(
            Defaults(
                parse_mode=ParseMode.HTML,
                link_preview_options=LinkPreviewOptions(is_disabled=True),
            )
        )
        .post_init(handlers.setup_bot_profile)
        .build()
    )
    app.bot_data.update(settings=settings, db=db, monitor=monitor)
    handlers.register(app)
    app.job_queue.run_repeating(
        scheduled_check,
        interval=settings.check_interval,
        first=FIRST_CHECK_DELAY_SECONDS,
        name=handlers.CHECK_JOB_NAME,
    )
    return app


def main() -> None:
    try:
        settings = load_settings()
        configure_logging(settings.log_level)
        app = build_application(settings)
    except ConfigError as exc:
        print(f"❌ Configuración inválida: {exc}", file=sys.stderr)
        sys.exit(1)

    logging.getLogger(__name__).info(
        "🤖 Bot iniciado | portales: %s | cada %ss", ", ".join(settings.sources), settings.check_interval
    )
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
