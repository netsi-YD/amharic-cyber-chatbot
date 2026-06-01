import logging
from chatbot_core import get_response, run_scenario, evaluate_answer
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Store user language and conversation history in memory (in production, use a database)
user_lang = {}          # user_id -> "am"/"en"
user_history = {}       # user_id -> list of messages

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_lang[user_id] = "am"   # default Amharic
    user_history[user_id] = []
    await update.message.reply_text(
        "ሰላም! የሳይበር ደህንነት ረዳትህ ነኝ።\n"
        "Type /en for English, /am for Amharic, /scenario for a test.\n"
        "Ask me anything about online safety!"
    )

async def set_amharic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_lang[user_id] = "am"
    await update.message.reply_text("አማርኛ ተመርጧል።")

async def set_english(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_lang[user_id] = "en"
    await update.message.reply_text("English selected.")

async def scenario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = user_lang.get(user_id, "am")
    try:
        scenario_text = run_scenario(lang)
        await update.message.reply_text(scenario_text)
        # We need to wait for the user's answer – we'll store that a scenario is active
        context.user_data['awaiting_scenario_answer'] = scenario_text
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = user_lang.get(user_id, "am")
    user_text = update.message.text.strip()

    # Check if we're waiting for a scenario answer
    if context.user_data.get('awaiting_scenario_answer'):
        scenario_text = context.user_data.pop('awaiting_scenario_answer')
        try:
            feedback = evaluate_answer(scenario_text, user_text, lang)
            await update.message.reply_text(feedback)
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")
        return

    # Normal chat
    history = user_history.get(user_id, [])
    try:
        reply = get_response(user_text, lang, history)
        await update.message.reply_text(reply)
        # Update history
        history.append({"role": "user", "content": user_text})
        history.append({"role": "assistant", "content": reply})
        user_history[user_id] = history
    except Exception as e:
        await update.message.reply_text("Sorry, an error occurred. Please try again later.")

def main():
    import os
    from dotenv import load_dotenv
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set in .env")

    app = ApplicationBuilder().token(token).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("am", set_amharic))
    app.add_handler(CommandHandler("en", set_english))
    app.add_handler(CommandHandler("scenario", scenario))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot started. Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == "__main__":
    main()