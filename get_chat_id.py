from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from config import BOT_TOKEN

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("CHAT ID:", update.effective_chat.id)
    print("CHAT TITLE:", update.effective_chat.title)
    await update.message.reply_text(f"chat_id: {update.effective_chat.id}")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.ALL, get_id))
app.run_polling()
