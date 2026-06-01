import json
import os
import sys
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Allow importing chatbot_core from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from chatbot_core import get_response, run_scenario, evaluate_answer

user_lang = {}
user_history = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_lang[user_id] = "am"
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
        context.user_data['awaiting_scenario_answer'] = scenario_text
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = user_lang.get(user_id, "am")
    user_text = update.message.text.strip()

    if context.user_data.get('awaiting_scenario_answer'):
        scenario_text = context.user_data.pop('awaiting_scenario_answer')
        try:
            feedback = evaluate_answer(scenario_text, user_text, lang)
            await update.message.reply_text(feedback)
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")
        return

    history = user_history.get(user_id, [])
    try:
        reply = get_response(user_text, lang, history)
        await update.message.reply_text(reply)
        history.append({"role": "user", "content": user_text})
        history.append({"role": "assistant", "content": reply})
        user_history[user_id] = history
    except Exception as e:
        await update.message.reply_text("Sorry, an error occurred. Please try again later.")

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN not set")

application = ApplicationBuilder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("am", set_amharic))
application.add_handler(CommandHandler("en", set_english))
application.add_handler(CommandHandler("scenario", scenario))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Vercel serverless function entry point
async def handler(request):
    if request.method == "POST":
        body = await request.json()
        update = Update.de_json(body, application.bot)
        await application.process_update(update)
        return {"statusCode": 200, "body": "OK"}
    return {"statusCode": 200, "body": "Bot webhook is alive."}