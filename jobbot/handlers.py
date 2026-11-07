"""Comandos y botones del bot."""
from __future__ import annotations

import logging

from telegram import BotCommand, Update
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from . import messages
from .config import Settings
from .db import Database
from .monitor import JobMonitor

log = logging.getLogger(__name__)

DEFAULT_LATEST = 5
MAX_LATEST = 20
CHECK_JOB_NAME = "check-portals"

COMMANDS = [
    BotCommand("start", "Activar avisos de ofertas"),
    BotCommand("ultimas", "Ver las ofertas más recientes"),
    BotCommand("estado", "Suscripción y estado de portales"),
    BotCommand("stop", "Pausar avisos"),
    BotCommand("ayuda", "Cómo funciona el bot"),
]


# ---------- Acceso al estado compartido ----------
def _settings(context: ContextTypes.DEFAULT_TYPE) -> Settings:
    return context.bot_data["settings"]


def _db(context: ContextTypes.DEFAULT_TYPE) -> Database:
    return context.bot_data["db"]


def _monitor(context: ContextTypes.DEFAULT_TYPE) -> JobMonitor:
    return context.bot_data["monitor"]


def _search_label(settings: Settings) -> str:
    return f"{settings.search_query} en {settings.search_city.title()}"


# ---------- Pantallas reutilizadas por comandos y botones ----------
async def _send_latest(update: Update, context: ContextTypes.DEFAULT_TYPE, limit: int) -> None:
    for text in messages.latest(_db(context).latest_jobs(limit)):
        await update.effective_message.reply_text(text)


async def _send_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings, db, monitor = _settings(context), _db(context), _monitor(context)
    chat_id = update.effective_chat.id
    jobs = context.job_queue.get_jobs_by_name(CHECK_JOB_NAME) if context.job_queue else ()
    source_lines = [
        messages.source_line(name, s.ok, s.found, s.error) for name, s in monitor.state.sources.items()
    ]
    text = messages.status(
        subscribed=db.is_subscribed(chat_id),
        chat_id=chat_id,
        last_run=monitor.state.last_run,
        next_run=getattr(jobs[0], "next_t", None) if jobs else None,  # None si el scheduler no arrancó
        running=monitor.running,
        total_jobs=db.count_jobs(),
        source_lines=source_lines,
        subscribers=db.count_subscribers() if chat_id in settings.admin_chat_ids else None,
    )
    await update.effective_message.reply_text(text, reply_markup=messages.main_menu(db.is_subscribed(chat_id)))


async def _send_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    subscribed = _db(context).is_subscribed(update.effective_chat.id)
    await update.effective_message.reply_text(
        messages.help_text(_search_label(_settings(context))), reply_markup=messages.main_menu(subscribed)
    )


# ---------- Comandos ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = _settings(context)
    is_new = _db(context).add_subscriber(update.effective_chat.id)
    user = update.effective_user
    await update.effective_message.reply_text(
        messages.welcome(
            user.first_name if user else "",
            is_new=is_new,
            search=_search_label(settings),
            sources=[s.name for s in _monitor(context).sources],
            interval=settings.check_interval,
        ),
        reply_markup=messages.main_menu(subscribed=True),
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    was_subscribed = _db(context).remove_subscriber(update.effective_chat.id)
    await update.effective_message.reply_text(
        messages.unsubscribed(was_subscribed), reply_markup=messages.main_menu(subscribed=False)
    )


async def latest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    limit = DEFAULT_LATEST
    if context.args:
        try:
            limit = max(1, min(int(context.args[0]), MAX_LATEST))
        except ValueError:
            await update.effective_message.reply_text(
                f"Usa un número, por ejemplo <code>/ultimas 10</code> (máximo {MAX_LATEST})."
            )
            return
    await _send_latest(update, context, limit)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _send_status(update, context)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _send_help(update, context)


async def check_now(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/revisar — solo administradores: fuerza una revisión inmediata."""
    if update.effective_chat.id not in _settings(context).admin_chat_ids:
        await update.effective_message.reply_text(messages.admin_only())
        return
    monitor = _monitor(context)
    if monitor.running:
        await update.effective_message.reply_text("⏳ Ya hay una revisión en curso.")
        return
    progress = await update.effective_message.reply_text("🔄 Revisando portales…")
    found = await monitor.run(context.bot)
    await progress.edit_text(f"✅ Revisión completa: <b>{found}</b> ofertas nuevas.")


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(messages.unknown_command())


# ---------- Botones inline ----------
async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    db, chat_id = _db(context), update.effective_chat.id

    if query.data in (messages.CB_SUBSCRIBE, messages.CB_UNSUBSCRIBE):
        subscribe = query.data == messages.CB_SUBSCRIBE
        if subscribe:
            db.add_subscriber(chat_id)
        else:
            db.remove_subscriber(chat_id)
        await query.answer("🔔 Avisos activados" if subscribe else "🔕 Avisos pausados")
        try:
            await query.edit_message_reply_markup(messages.main_menu(subscribed=subscribe))
        except BadRequest:
            pass  # el teclado ya estaba así
        return

    await query.answer()
    if query.data == messages.CB_LATEST:
        await _send_latest(update, context, DEFAULT_LATEST)
    elif query.data == messages.CB_STATUS:
        await _send_status(update, context)
    elif query.data == messages.CB_HELP:
        await _send_help(update, context)


# ---------- Errores ----------
async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.error("Error procesando una actualización", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(messages.generic_error())
        except Exception:  # noqa: BLE001 - no fallar dentro del manejador de errores
            pass


# ---------- Registro ----------
def register(app: Application) -> None:
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler(["stop", "pausar"], stop))
    app.add_handler(CommandHandler(["ultimas", "latest"], latest))
    app.add_handler(CommandHandler(["estado", "status"], status))
    app.add_handler(CommandHandler(["ayuda", "help"], help_command))
    app.add_handler(CommandHandler("revisar", check_now))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))
    app.add_error_handler(on_error)


async def setup_bot_profile(app: Application) -> None:
    """Menú de comandos y descripción visibles en Telegram."""
    settings: Settings = app.bot_data["settings"]
    try:
        await app.bot.set_my_commands(COMMANDS)
        await app.bot.set_my_short_description(
            f"Avisos de ofertas nuevas de {_search_label(settings)}."
        )
        await app.bot.set_my_description(
            f"Te aviso en cuanto aparecen ofertas nuevas de {_search_label(settings)} "
            "en los principales portales de empleo, sin duplicados. Pulsa Iniciar para activar los avisos."
        )
    except Exception as exc:  # noqa: BLE001 - no es crítico para el funcionamiento
        log.warning("No se pudo configurar el perfil del bot: %s", exc)
