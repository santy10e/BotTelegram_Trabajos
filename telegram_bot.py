from datetime import datetime
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8344348194:AAHV3KUSAjjAO7-kmyWem5RflNeCbgwhnUQ"
DB = "jobs.db"

def db_exec(query, params=()):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    db_exec(
        "INSERT OR IGNORE INTO subscribers (chat_id, created_at) VALUES (?, ?)",
        (chat_id, datetime.utcnow().isoformat())
    )
    await update.message.reply_text(
        "🤖 Bot activo.\n"
        "Recibirás ofertas de tecnología en Quito.\n\n"
        "Usa /stop para salir."
    )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    db_exec("DELETE FROM subscribers WHERE chat_id = ?", (chat_id,))
    await update.message.reply_text("Te has desuscrito.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM subscribers")
    count = c.fetchone()[0]
    conn.close()
    await update.message.reply_text(f" Suscriptores: {count}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("status", status))

    print("🤖 Bot de Telegram iniciado")
    app.run_polling()

if __name__ == "__main__":
    main()