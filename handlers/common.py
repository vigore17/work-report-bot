from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from db import is_admin
from keyboards import get_main_menu
from services.access import get_user_store_role, get_global_role
from handlers.onboarding import setup_keyboard, store_admin_menu, join_by_invite


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    if chat.type != "private":
        if update.message:
            await update.message.reply_text("Пожалуйста, используйте бота в личных сообщениях.")
        return

    if context.args:
        arg = context.args[0]
        if arg.startswith("join_"):
            code = arg.replace("join_", "", 1)
            await join_by_invite(update, context, code)
            return

    user = update.effective_user
    global_role = get_global_role(user.id)
    store_role = get_user_store_role(user.id)

    if global_role == "super_admin":
        await update.message.reply_text(
            "Привет, главный админ. Выбери действие:",
            reply_markup=get_main_menu(True),
        )
        return

    if store_role:
        if store_role["role"] == "store_admin":
            await update.message.reply_text(
                f"Привет. Вы директор магазина {store_role['name']}.",
                reply_markup=store_admin_menu(),
            )
            return

        await update.message.reply_text(
            f"Привет. Вы сотрудник магазина {store_role['name']}.",
            reply_markup=get_main_menu(False),
        )
        return

    await update.message.reply_text(
        "Привет. У вас пока нет магазина.\n\n"
        "Если вы директор — настройте магазин.\n"
        "Если вы сотрудник — попросите директора прислать ссылку-приглашение.",
        reply_markup=setup_keyboard(),
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
        "Директор может настроить магазин и пригласить сотрудников.\n"
        "Сотрудник отправляет отчёт без выбора магазина."
    )
    await update.message.reply_text(text)
