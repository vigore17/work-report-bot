from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from db import is_admin, add_store, get_active_stores, update_store_plans, update_store_chat
from keyboards import get_admin_menu

from states import (
    ADMIN_MENU,
)


async def admin_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(update.effective_user.id):
        await query.message.reply_text("Нет доступа.")
        return

    await query.message.reply_text("Админ-панель:", reply_markup=get_admin_menu())
    return ADMIN_MENU
