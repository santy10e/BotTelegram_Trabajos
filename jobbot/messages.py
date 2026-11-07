"""Textos y teclados del bot (HTML de Telegram). Todo texto externo se escapa."""
from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
from html import escape

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .models import Job

MAX_MESSAGE_LENGTH = 4096

# Datos de callback de los botones inline
CB_LATEST = "latest"
CB_STATUS = "status"
CB_HELP = "help"
CB_SUBSCRIBE = "sub"
CB_UNSUBSCRIBE = "unsub"


# ---------- Utilidades de formato ----------
def humanize_seconds(seconds: float) -> str:
    seconds = int(max(seconds, 0))
    if seconds < 60:
        return f"{seconds} s"
    minutes = round(seconds / 60)
    if minutes < 60:
        return f"{minutes} min"
    hours, minutes = divmod(minutes, 60)
    return f"{hours} h {minutes} min" if minutes else f"{hours} h"


def time_ago(moment: datetime | None) -> str:
    if moment is None:
        return "todavía no"
    elapsed = (datetime.now(timezone.utc) - moment).total_seconds()
    return "hace un momento" if elapsed < 60 else f"hace {humanize_seconds(elapsed)}"


def time_until(moment: datetime | None) -> str:
    if moment is None:
        return "no programada"
    return f"en {humanize_seconds((moment - datetime.now(timezone.utc)).total_seconds())}"


def chunk_lines(header: str, blocks: Iterable[str], limit: int = MAX_MESSAGE_LENGTH) -> list[str]:
    """Agrupa bloques en mensajes que no superen el límite de Telegram."""
    messages, current = [], header
    for block in blocks:
        candidate = f"{current}\n\n{block}"
        if len(candidate) > limit and current != header:
            messages.append(current)
            current = block
        else:
            current = candidate
    messages.append(current)
    return messages


# ---------- Ofertas ----------
def job_card(job: Job) -> str:
    return (
        f"🆕 <b>{escape(job.title)}</b>\n"
        f"🏢 {escape(job.company)}\n"
        f"📍 {escape(job.location)}\n"
        f"🌐 <i>{escape(job.source)}</i>"
    )


def job_keyboard(job: Job) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Ver oferta", url=job.link)]])


def _job_line(index: int, job: Job) -> str:
    return (
        f"{index}. <a href=\"{escape(job.link, quote=True)}\"><b>{escape(job.title)}</b></a>\n"
        f"    🏢 {escape(job.company)} · 📍 {escape(job.location)} · <i>{escape(job.source)}</i>"
    )


def job_list(header: str, jobs: list[Job]) -> list[str]:
    return chunk_lines(header, (_job_line(i, job) for i, job in enumerate(jobs, 1)))


def digest(jobs: list[Job]) -> list[str]:
    return job_list(f"🆕 <b>{len(jobs)} ofertas nuevas</b>\nToca un título para abrirla.", jobs)


def latest(jobs: list[Job]) -> list[str]:
    if not jobs:
        return [
            "📭 <b>Aún no hay ofertas registradas.</b>\n\n"
            "La primera revisión se hace al iniciar el bot. Vuelve a intentarlo en unos minutos."
        ]
    return job_list(f"📋 <b>Últimas {len(jobs)} ofertas</b>", jobs)


# ---------- Pantallas ----------
def _commands_help() -> str:
    return (
        "<b>Comandos</b>\n"
        "/ultimas — ver las ofertas más recientes (ej. <code>/ultimas 10</code>)\n"
        "/estado — tu suscripción y el estado de los portales\n"
        "/stop — pausar los avisos\n"
        "/start — volver a activarlos\n"
        "/ayuda — mostrar esta ayuda"
    )


def welcome(first_name: str, *, is_new: bool, search: str, sources: list[str], interval: int) -> str:
    greeting = f"👋 <b>¡Hola, {escape(first_name)}!</b>" if is_new else "✅ <b>Ya tienes los avisos activados.</b>"
    return (
        f"{greeting}\n\n"
        f"Te avisaré en cuanto aparezcan <b>ofertas nuevas de {escape(search)}</b>.\n\n"
        f"🔎 Portales: {escape(', '.join(sources))}\n"
        f"⏱ Reviso cada {humanize_seconds(interval)} y solo te envío lo nuevo, sin duplicados.\n\n"
        f"{_commands_help()}"
    )


def help_text(search: str) -> str:
    return (
        "ℹ️ <b>¿Cómo funciono?</b>\n\n"
        f"Reviso periódicamente los portales de empleo buscando <b>{escape(search)}</b>. "
        "Cada oferta nueva te llega con un botón para abrirla; si aparecen muchas a la vez, "
        "te las envío juntas en un solo resumen.\n\n"
        f"{_commands_help()}"
    )


def unsubscribed(was_subscribed: bool) -> str:
    if was_subscribed:
        return "🔕 <b>Avisos pausados.</b>\nNo recibirás más ofertas. Puedes reactivarlos cuando quieras."
    return "ℹ️ No tenías los avisos activados."


def status(
    *,
    subscribed: bool,
    chat_id: int,
    last_run: datetime | None,
    next_run: datetime | None,
    running: bool,
    total_jobs: int,
    source_lines: list[str],
    subscribers: int | None,
) -> str:
    lines = [
        "📊 <b>Estado</b>",
        "",
        f"{'🔔' if subscribed else '🔕'} Avisos: <b>{'activados' if subscribed else 'pausados'}</b>",
        f"🕒 Última revisión: {'en curso…' if running else time_ago(last_run)}",
        f"⏭ Próxima revisión: {time_until(next_run)}",
        f"🗂 Ofertas registradas: <b>{total_jobs}</b>",
    ]
    if source_lines:
        lines += ["", "<b>Portales (última revisión)</b>", *source_lines]
    if subscribers is not None:
        lines += ["", f"👥 Suscriptores: <b>{subscribers}</b>"]
    lines += ["", f"🆔 Tu chat_id: <code>{chat_id}</code>"]
    return "\n".join(lines)


def source_line(name: str, ok: bool, found: int, error: str) -> str:
    if ok:
        return f"✅ {escape(name)} — {found} ofertas"
    return f"⚠️ {escape(name)} — {escape(error)}"


def unknown_command() -> str:
    return "🤔 No reconozco ese comando. Usa /ayuda para ver las opciones."


def admin_only() -> str:
    return "🔒 Este comando es solo para administradores."


def generic_error() -> str:
    return "😕 Algo salió mal procesando tu solicitud. Inténtalo de nuevo en un momento."


# ---------- Teclados ----------
def main_menu(subscribed: bool) -> InlineKeyboardMarkup:
    toggle = (
        InlineKeyboardButton("🔕 Pausar avisos", callback_data=CB_UNSUBSCRIBE)
        if subscribed
        else InlineKeyboardButton("🔔 Activar avisos", callback_data=CB_SUBSCRIBE)
    )
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📋 Últimas ofertas", callback_data=CB_LATEST),
                InlineKeyboardButton("📊 Estado", callback_data=CB_STATUS),
            ],
            [toggle, InlineKeyboardButton("ℹ️ Ayuda", callback_data=CB_HELP)],
        ]
    )
