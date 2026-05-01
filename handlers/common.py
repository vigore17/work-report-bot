from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from db import is_admin
from keyboards import get_main_menu


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    admin = is_admin(user.id)

    if update.message:
        await update.message.reply_text(
            "Привет. Выбери действие:",
            reply_markup=get_main_menu(admin),
        )
    elif update.callback_query:
        await update.callback_query.message.reply_text(
            "Привет. Выбери действие:",
            reply_markup=get_main_menu(admin),
        )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    if update.message:
        await update.message.reply_text("Действие отменено. Напиши /start")
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text("Действие отменено. Напиши /start")

    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Бот для ежедневных отчётов.\n\n"
        "Как работать:\n"
        "1. Нажми «Отправить отчёт»\n"
        "2. Выбери магазин\n"
        "3. Введи суммы по очереди\n"
        "4. Подтверди отправку"
    )
    await update.message.reply_text(text)
