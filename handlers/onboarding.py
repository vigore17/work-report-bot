import uuid
from datetime import datetime
from config import DEFAULT_REPORT_CHAT_ID, DEFAULT_BOSS_USER_ID

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from db import (
    create_store_v21,
    create_store_invite,
    get_invite_by_code,
    add_user_to_store,
    get_store_by_owner,
    set_acquiring_base,
)
from utils import parse_int_amount
from states import (
    SETUP_STORE_NAME,
    SETUP_DAILY_PLAN,
    SETUP_MONTHLY_ACQUIRING_PLAN,
    SETUP_ACQUIRING_BASE,
    SETUP_REPORT_TIME,
    SETUP_REPORT_CHAT_ID,
    SETUP_BOSS_ID,
    SETUP_CONFIRM,
)


def setup_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Настроить магазин", callback_data="setup_store")],
    ])


def store_admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Отправить отчёт", callback_data="send_report")],
        [InlineKeyboardButton("🔗 Пригласить сотрудника", callback_data="create_employee_invite")],
    ])


def setup_confirm_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Создать магазин", callback_data="confirm_setup_store")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_setup_store")],
    ])


async def setup_store_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data.clear()
    await query.message.reply_text("Введите название магазина:")
    return SETUP_STORE_NAME


async def setup_store_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["setup_store_name"] = update.message.text.strip()
    await update.message.reply_text("Введите дневной план магазина. Например: 80000")
    return SETUP_DAILY_PLAN


async def setup_daily_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["setup_daily_plan"] = parse_int_amount(update.message.text)
    except ValueError:
        await update.message.reply_text("Введите число. Например: 80000")
        return SETUP_DAILY_PLAN

    await update.message.reply_text("Введите план эквайринга на месяц. Например: 350000")
    return SETUP_MONTHLY_ACQUIRING_PLAN


async def setup_monthly_acquiring_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["setup_monthly_acquiring_plan"] = parse_int_amount(update.message.text)
    except ValueError:
        await update.message.reply_text("Введите число. Например: 350000")
        return SETUP_MONTHLY_ACQUIRING_PLAN

    await update.message.reply_text(
        "Введите текущий накопленный эквайринг за месяц до запуска бота.\n"
        "Если с нуля — введите 0."
    )
    return SETUP_ACQUIRING_BASE


async def setup_acquiring_base(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["setup_acquiring_base"] = parse_int_amount(update.message.text)
    except ValueError:
        await update.message.reply_text("Введите число. Например: 121254 или 0")
        return SETUP_ACQUIRING_BASE

    await update.message.reply_text("Введите время отправки отчёта. Например: 19:55")
    return SETUP_REPORT_TIME


async def setup_report_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text.strip()

    try:
        datetime.strptime(value, "%H:%M")
    except ValueError:
        await update.message.reply_text("Введите время в формате ЧЧ:ММ. Например: 19:55")
        return SETUP_REPORT_TIME

    context.user_data["setup_report_time"] = value
    context.user_data["setup_report_chat_id"] = DEFAULT_REPORT_CHAT_ID
    context.user_data["setup_boss_user_id"] = DEFAULT_BOSS_USER_ID

    text = (
        "Проверь настройки:\n\n"
        f"Магазин: {context.user_data['setup_store_name']}\n"
        f"Дневной план: {context.user_data['setup_daily_plan']}\n"
        f"План эквайринга: {context.user_data['setup_monthly_acquiring_plan']}\n"
        f"Стартовый эквайринг: {context.user_data['setup_acquiring_base']}\n"
        f"Время отправки: {context.user_data['setup_report_time']}\n\n"
        "Группа отчётов и босс будут назначены автоматически."
    )

    await update.message.reply_text(text, reply_markup=setup_confirm_keyboard())
    return SETUP_CONFIRM


async def setup_report_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    try:
        report_chat_id = int(text)
    except ValueError:
        await update.message.reply_text("Введите число. Например: -1001234567890 или 0")
        return SETUP_REPORT_CHAT_ID

    context.user_data["setup_report_chat_id"] = None if report_chat_id == 0 else report_chat_id

    await update.message.reply_text(
        "Введите Telegram user_id босса для второй части отчёта.\n"
        "Если пока не знаете — введите 0."
    )
    return SETUP_BOSS_ID


async def setup_boss_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    try:
        boss_user_id = int(text)
    except ValueError:
        await update.message.reply_text("Введите число или 0.")
        return SETUP_BOSS_ID

    context.user_data["setup_boss_user_id"] = None if boss_user_id == 0 else boss_user_id

    text = (
        "Проверь настройки:\n\n"
        f"Магазин: {context.user_data['setup_store_name']}\n"
        f"Дневной план: {context.user_data['setup_daily_plan']}\n"
        f"План эквайринга: {context.user_data['setup_monthly_acquiring_plan']}\n"
        f"Стартовый эквайринг: {context.user_data['setup_acquiring_base']}\n"
        f"Время отправки: {context.user_data['setup_report_time']}\n"
        f"chat_id группы: {context.user_data['setup_report_chat_id']}\n"
        f"boss_user_id: {context.user_data['setup_boss_user_id']}\n"
    )

    await update.message.reply_text(text, reply_markup=setup_confirm_keyboard())
    return SETUP_CONFIRM


async def confirm_setup_store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "cancel_setup_store":
        context.user_data.clear()
        await query.message.reply_text("Настройка отменена.")
        return ConversationHandler.END

    user = update.effective_user

    store_id = create_store_v21(
        name=context.user_data["setup_store_name"],
        owner_user_id=user.id,
        daily_plan=context.user_data["setup_daily_plan"],
        monthly_acquiring_plan=context.user_data["setup_monthly_acquiring_plan"],
        report_chat_id=context.user_data["setup_report_chat_id"],
        report_send_time=context.user_data["setup_report_time"],
        boss_user_id=context.user_data["setup_boss_user_id"],
    )

    month_key = datetime.now().strftime("%Y-%m")
    set_acquiring_base(
        store_id=store_id,
        month_key=month_key,
        base_amount=context.user_data["setup_acquiring_base"],
        comment="Стартовый эквайринг при настройке магазина",
    )

    context.user_data.clear()

    await query.message.reply_text(
        "✅ Магазин создан. Вы назначены директором магазина.",
        reply_markup=store_admin_menu(),
    )

    return ConversationHandler.END


async def create_employee_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    store = get_store_by_owner(user_id)

    if not store:
        await query.message.reply_text("У вас нет магазина, где вы являетесь директором.")
        return

    code = uuid.uuid4().hex[:8].upper()
    create_store_invite(code=code, store_id=store["id"], created_by=user_id, role="employee")

    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start=join_{code}"

    await query.message.reply_text(
        f"Ссылка для сотрудника магазина {store['name']}:\n\n{link}\n\n"
        "Отправьте её сотруднику. Когда он нажмёт Start, бот сам привяжет его к магазину."
    )


async def join_by_invite(update: Update, context: ContextTypes.DEFAULT_TYPE, code: str):
    invite = get_invite_by_code(code)

    if not invite:
        await update.message.reply_text("Ссылка недействительна или отключена.")
        return

    user = update.effective_user

    add_user_to_store(
        user_id=user.id,
        store_id=invite["store_id"],
        role=invite["role"],
        username=user.username,
    )

    await update.message.reply_text(
        f"✅ Вы добавлены как сотрудник магазина {invite['store_name']}.\n\n"
        "Теперь нажмите «Отправить отчёт», и бот сразу начнёт принимать данные.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Отправить отчёт", callback_data="send_report")]
        ])
    )
