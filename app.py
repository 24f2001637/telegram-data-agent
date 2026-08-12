import os
import json
import threading
import asyncio
from dotenv import load_dotenv
from flask import Flask, send_file

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)

from ai import ask_ai
from logger import write_log
from data_agent import find_url, load_dataset

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))
BASE_URL = (os.getenv("BASE_URL") or os.getenv("RENDER_EXTERNAL_URL") or f"http://localhost:{PORT}").rstrip("/")

# ---------------- Flask Server ----------------

server = Flask(__name__)

@server.route("/")
def home():
    return "Telegram Data Agent is running!"

@server.route("/logs/run.jsonl")
@server.route("/run.jsonl")
def logs():
    log_path = "logs/run.jsonl"
    if not os.path.exists(log_path):
        os.makedirs("logs", exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as f:
            pass
    return send_file(log_path, mimetype="text/plain")

# ---------------- Telegram Bot ----------------

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):

    question = update.message.text

    write_log("user", question)

    log_url = f"{BASE_URL}/logs/run.jsonl"

    try:
        url = find_url(question)

        if url:
            df = load_dataset(url)
            answer = ask_ai(question, df, log_url=log_url)
        else:
            answer = ask_ai(question, log_url=log_url)

    except Exception as e:
        write_log("error", str(e))
        answer = json.dumps({
            "answer": "Error processing query. Please try again later.",
            "log_url": log_url
        })

    write_log("assistant", answer)

    await update.message.reply_text(answer)


def run_bot():
    asyncio.set_event_loop(asyncio.new_event_loop())

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, reply)
    )

    print("Bot is running...")

    app.run_polling(stop_signals=None)
# ---------------- Main ----------------

if __name__ == "__main__":

    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    server.run(host="0.0.0.0", port=PORT)
