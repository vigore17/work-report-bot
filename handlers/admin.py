from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from db import (
    is_admin,
    get_store_by_id,
    update_store_plans,
    set_acquiring_base,
    get_store_month_stats,
)
from keyboards import get_admin_menu, get_main_menu
from services.access import get_user_stores, is_super_admin
from utils import parse_int_amount
from states import (
    ADMIN_MENU,
    ADMIN_SET_PLANS_STORE,
    ADMIN_SET_PLANS_VALUE,
)


def stores_keyboard(stores, prefix: str):
    buttons = []

    for store in stores:
        buttons.append([
            InlineKeyboardButton(store["name"], callback_data=f"{prefix}_{store['id']}")
        ])

    buttons.append([InlineKeyboardButton("❌ Отмена", callback_data="admin_cancel")])

    return InlineKeyboardMarkup(buttons)


async def admin_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    stores = get_user_stores(user_id)

    if not is_admin(user_id) and not is_super_admin(user_id) and not stores:
        await query.message.reply_text("Нет доступа.")
        return

    await query.message.reply_text("Админ-панель:", reply_markup=get_admin_menu())
    return ADMIN_MENU


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    await query.message.reply_text(
        "Главное меню:",
        reply_markup=get_main_menu(is_admin(user_id) or is_super_admin(user_id)),
    )


async def admin_update_plans_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    stores = get_user_stores(user_id)

    if not stores:
        await query.message.reply_text("У вас нет магазинов для обновления планов.")
        return ConversationHandler.END

    context.user_data.clear()

    if len(stores) == 1:
        store = stores[0]
        context.user_data["admin_plan_store_id"] = store["id"]
        context.user_data["admin_plan_store_name"] = store["name"]

        await query.message.reply_text(
            f"Магазин: {store['name']}\n\n"
            "Введите новые данные одной строкой:\n"
            "дневной_план план_эквайринга стартовый_эквайринг\n\n"
            "Пример:\n"
            "80000 350000 0"
        )
        return ADMIN_SET_PLANS_VALUE

    await query.message.reply_text(
        "Выбери магазин для обновления планов:",
        reply_markup=stores_keyboard(stores, "admin_plan_store")
    )

    return ADMIN_SET_PLANS_STORE


async def admin_select_plan_store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "admin_cancel":
        context.user_data.clear()
        await query.message.reply_text("Действие отменено.")
        return ConversationHandler.END

    store_id = int(query.data.replace("admin_plan_store_", "", 1))
    user_id = update.effective_user.id
    stores = get_user_stores(user_id)

    selected_store = None
    for store in stores:
        if store["id"] == store_id:
            selected_store = store
            break

    if not selected_store:
        await query.message.reply_text("⛔ Нет доступа к этому магазину.")
        return ConversationHandler.END

    context.user_data["admin_plan_store_id"] = selected_store["id"]
    context.user_data["admin_plan_store_name"] = selected_store["name"]

    await query.message.reply_text(
        f"Магазин: {selected_store['name']}\n\n"
        "Введите новые данные одной строкой:\n"
        "дневной_план план_эквайринга стартовый_эквайринг\n\n"
        "Пример:\n"
        "80000 350000 0"
    )

    return ADMIN_SET_PLANS_VALUE


async def admin_save_plans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    parts = text.replace(",", " ").split()

    if len(parts) != 3:
        await update.message.reply_text(
            "Нужно ввести 3 числа через пробел.\n"
            "Пример:\n"
            "80000 350000 0"
        )
        return ADMIN_SET_PLANS_VALUE

    try:
        daily_plan = parse_int_amount(parts[0])
        monthly_acquiring_plan = parse_int_amount(parts[1])
        acquiring_base = parse_int_amount(parts[2])
    except ValueError:
        await update.message.reply_text(
            "Все значения должны быть числами.\n"
            "Пример:\n"
            "80000 350000 0"
        )
        return ADMIN_SET_PLANS_VALUE

    store_id = context.user_data["admin_plan_store_id"]
    store_name = context.user_data["admin_plan_store_name"]
    month_key = datetime.now().strftime("%Y-%m")

    update_store_plans(store_id, daily_plan, monthly_acquiring_plan)
    set_acquiring_base(
        store_id=store_id,
        month_key=month_key,
        base_amount=acquiring_base,
        comment="Обновлено через админ-панель",
    )

    context.user_data.clear()

    await update.message.reply_text(
        f"✅ Планы обновлены.\n\n"
        f"Магазин: {store_name}\n"
        f"Дневной план: {daily_plan}\n"
        f"План эквайринга: {monthly_acquiring_plan}\n"
        f"Стартовый эквайринг за {month_key}: {acquiring_base}"
    )

    return ConversationHandler.END


async def admin_store_stats_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    stores = get_user_stores(user_id)

    if not stores:
        await query.message.reply_text("У вас нет магазинов для просмотра статистики.")
        return

    if len(stores) == 1:
        await send_store_stats(query, stores[0])
        return

    await query.message.reply_text(
        "Выбери магазин для статистики:",
        reply_markup=stores_keyboard(stores, "admin_stats_store")
    )


async def admin_select_stats_store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "admin_cancel":
        await query.message.reply_text("Действие отменено.")
        return

    store_id = int(query.data.replace("admin_stats_store_", "", 1))
    user_id = update.effective_user.id
    stores = get_user_stores(user_id)

    selected_store = None
    for store in stores:
        if store["id"] == store_id:
            selected_store = store
            break

    if not selected_store:
        await query.message.reply_text("⛔ Нет доступа к этому магазину.")
        return

    await send_store_stats(query, selected_store)


async def send_store_stats(query, store):
    month_key = datetime.now().strftime("%Y-%m")
    stats = get_store_month_stats(store["id"], month_key)

    reports_count = stats["reports_count"] or 0
    gross_total = stats["gross_total"] or 0
    daily_plan = stats["daily_plan"] or 0
    retail_total = stats["retail_total"] or 0
    wholesale_total = stats["wholesale_total"] or 0
    acquiring_total = stats["acquiring_total"] or 0
    im_orders = stats["im_orders"] or 0
    cash_total = stats["cash_total"] or 0

    percent = round((gross_total / daily_plan) * 100) if daily_plan else 0

    await query.message.reply_text(
        f"📊 Статистика магазина за {month_key}\n\n"
        f"🏬 {store['name']}\n"
        f"Отчётов: {reports_count}\n\n"
        f"Общий: {daily_plan}/{gross_total}/{percent}%\n"
        f"Розница: {retail_total}\n"
        f"Опт: {wholesale_total}\n"
        f"Эквайринг: {acquiring_total}\n"
        f"Заказы ИМ: {im_orders}\n"
        f"Наличные: {cash_total}"
    )
