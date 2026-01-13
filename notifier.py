import asyncio
import sqlite3
from telegram import Bot

TOKEN = "8344348194:AAHV3KUSAjjAO7-kmyWem5RflNeCbgwhnUQ"
DB = "jobs.db"

bot = Bot(token=TOKEN)

# ---------- EVENT LOOP DEDICADO ----------
_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)

async def _send(chat_id, message):
    await bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode="Markdown"
    )

def notify(job):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT chat_id FROM subscribers")
    subscribers = c.fetchall()
    conn.close()

    message = (
        f"💼 *Nueva oferta detectada*\n\n"
        f"*Puesto:* {job['title']}\n"
        f"*Empresa:* {job['company']}\n"
        f"*Ubicación:* {job['location']}\n"
        f"*Fuente:* {job['source']}\n\n"
        f"🔗 {job['link']}"
    )

    for (chat_id,) in subscribers:
        try:
            _loop.run_until_complete(_send(chat_id, message))
        except Exception as e:
            print("Telegram error:", e)