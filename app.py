import os
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

# ---------------- Flask Server ----------------

server = Flask(__name__)

@server.route("/")
def home():
    return "Telegram Data Agent is running!"

@server.route("/logs/run.jsonl")
def logs():
    return send_file("logs/run.jsonl", mimetype="application/json")

# ---------------- Telegram Bot ----------------

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):

    question = update.message.text

    write_log("user", question)

    try:
        url = find_url(question)

        if url:
            df = load_dataset(url)
            answer = ask_ai(question, df)
        else:
            answer = ask_ai(question)

    except Exception as e:
        write_log("error", str(e))
        answer = ask_ai(question)

    write_log("assistant", answer)

    await update.message.reply_text(answer)


def run_bot():
    asyncio.set_event_loop(asyncio.new_event_loop())

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, reply)
    )

    print("Bot is running...")
    app.run_polling()
# ---------------- Main ----------------

if __name__ == "__main__":

    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    server.run(host="0.0.0.0", port=PORT)