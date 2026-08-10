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

PUBLIC_LOG_URL = os.getenv(
    "PUBLIC_LOG_URL",
    "https://telegram-data-agent.onrender.com/logs/run.jsonl"
)


# =========================================================
# Flask server
# =========================================================

server = Flask(__name__)


@server.route("/")
def home():
    return "Telegram Data Agent is running!"


@server.route("/logs/run.jsonl")
def logs():

    log_path = os.path.join("logs", "run.jsonl")

    if not os.path.exists(log_path):
        return "", 404

    return send_file(
        log_path,
        mimetype="application/json"
    )


# =========================================================
# Telegram bot
# =========================================================

async def reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message or not update.message.text:
        return

    question = update.message.text.strip()

    write_log(
        "user",
        question
    )

    # -----------------------------------------------------
    # Conversation history
    # -----------------------------------------------------

    history = context.user_data.setdefault(
        "history",
        []
    )

    history.append({
        "role": "user",
        "content": question
    })

    # Keep last 10 messages
    if len(history) > 10:
        history[:] = history[-10:]

    conversation = "\n\n".join(
        f"{message['role'].upper()}: "
        f"{message['content']}"
        for message in history
    )

    try:

        # -------------------------------------------------
        # Find dataset URL
        # -------------------------------------------------

        url = find_url(question)

        if url:

            dataframe = load_dataset(url)

            ai_answer = ask_ai(
                conversation,
                dataframe
            )

        else:

            ai_answer = ask_ai(
                conversation
            )

        # -------------------------------------------------
        # Parse model output
        # -------------------------------------------------

        try:

            answer = json.loads(
                ai_answer
            )

        except json.JSONDecodeError:

            # Try extracting JSON from accidental
            # surrounding text.

            start = ai_answer.find("{")
            end = ai_answer.rfind("}")

            if (
                start != -1
                and end != -1
                and end > start
            ):

                answer = json.loads(
                    ai_answer[start:end + 1]
                )

            else:

                answer = ai_answer

        # -------------------------------------------------
        # Required Project 1 response
        # -------------------------------------------------

        result = {
            "answer": answer,
            "log_url": PUBLIC_LOG_URL
        }

        write_log(
            "assistant",
            result
        )

        response = json.dumps(
            result,
            ensure_ascii=False,
            separators=(",", ":")
        )

        await update.message.reply_text(
            response
        )

    except Exception as e:

        write_log(
            "error",
            str(e)
        )

        result = {
            "answer": None,
            "log_url": PUBLIC_LOG_URL
        }

        await update.message.reply_text(
            json.dumps(
                result,
                separators=(",", ":")
            )
        )


# =========================================================
# Bot runner
# =========================================================

def run_bot():

    loop = asyncio.new_event_loop()

    asyncio.set_event_loop(loop)

    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            reply
        )
    )

    print("Telegram bot is running...")

    application.run_polling(
        stop_signals=None
    )


# =========================================================
# Main
# =========================================================

if __name__ == "__main__":

    bot_thread = threading.Thread(
        target=run_bot,
        daemon=True
    )

    bot_thread.start()

    print(
        f"Flask server running on port {PORT}"
    )

    server.run(
        host="0.0.0.0",
        port=PORT
    )