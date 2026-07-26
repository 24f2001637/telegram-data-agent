import os
from dotenv import load_dotenv

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

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")


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

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

print("Bot is running...")

app.run_polling()