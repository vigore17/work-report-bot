from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db import get_daily_stats, get_month_stats, get_available_months
from services.access import is_boss, is_super_admin


def boss_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Статистика за сегодня", callback_data="boss_stats_today")],
        [InlineKeyboardButton("📅 Статистика за месяц", callback_data="boss_stats_month_current")],
        [InlineKeyboardButton("🗓 Предыдущие месяцы", callback_data="boss_stats_months_list")],
    ])


def format_daily_stats(rows, report_date: str) -> str:
    if not rows:
        return f"📊 Статистика за {report_date}\n\nОтчётов пока нет."

    total_plan = 0
    total_gross = 0
    total_retail = 0
    total_wholesale = 0
    total_acquiring = 0
    total_im_orders = 0
    lines = [f"📊 Статистика за {report_date}\n"]

    for row in rows:
        plan = row["daily_plan"] or 0
        gross = row["gross_total"] or 0
        percent = round((gross / plan) * 100) if plan else 0

        total_plan += plan
        total_gross += gross
        total_retail += row["retail_total"] or 0
        total_wholesale += row["wholesale_total"] or 0
        total_acquiring += row["acquiring_total"] or 0
        total_im_orders += row["im_orders"] or 0

        lines.append(
            f"🏬 {row['store_name']}\n"
            f"Общий: {plan}/{gross}/{percent}%\n"
            f"Розница: {row['retail_total']}\n"
            f"Опт: {row['wholesale_total']}\n"
            f"Эквайринг: {row['acquiring_total']}\n"
            f"Заказы ИМ: {row['im_orders']}\n"
        )

    total_percent = round((total_gross / total_plan) * 100) if total_plan else 0

    lines.append(
        "ИТОГО:\n"
        f"Общий: {total_plan}/{total_gross}/{total_percent}%\n"
        f"Розница: {total_retail}\n"
        f"Опт: {total_wholesale}\n"
        f"Эквайринг: {total_acquiring}\n"
        f"Заказы ИМ: {total_im_orders}"
    )

    return "\n".join(lines)


def format_month_stats(rows, month_key: str) -> str:
    if not rows:
        return f"📅 Статистика за {month_key}\n\nОтчётов пока нет."

    total_plan = 0
    total_gross = 0
    total_retail = 0
    total_wholesale = 0
    total_acquiring = 0
    total_im_orders = 0

    lines = [f"📅 Статистика за {month_key}\n"]

    for row in rows:
        plan = row["daily_plan"] or 0
        gross = row["gross_total"] or 0
        percent = round((gross / plan) * 100) if plan else 0

        total_plan += plan
        total_gross += gross
        total_retail += row["retail_total"] or 0
        total_wholesale += row["wholesale_total"] or 0
        total_acquiring += row["acquiring_total"] or 0
        total_im_orders += row["im_orders"] or 0

        lines.append(
            f"🏬 {row['store_name']}\n"
            f"Отчётов: {row['reports_count']}\n"
            f"Общий: {plan}/{gross}/{percent}%\n"
            f"Розница: {row['retail_total']}\n"
            f"Опт: {row['wholesale_total']}\n"
            f"Эквайринг: {row['acquiring_total']}\n"
            f"Заказы ИМ: {row['im_orders']}\n"
        )

    total_percent = round((total_gross / total_plan) * 100) if total_plan else 0

    lines.append(
        "ИТОГО ЗА МЕСЯЦ:\n"
        f"Общий: {total_plan}/{total_gross}/{total_percent}%\n"
        f"Розница: {total_retail}\n"
        f"Опт: {total_wholesale}\n"
        f"Эквайринг: {total_acquiring}\n"
        f"Заказы ИМ: {total_im_orders}"
    )

    return "\n".join(lines)


async def boss_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    if not is_boss(user_id) and not is_super_admin(user_id):
        await query.message.reply_text("⛔ Нет доступа.")
        return

    await query.message.reply_text(
        "Панель босса:",
        reply_markup=boss_menu_keyboard()
    )


async def boss_stats_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    if not is_boss(user_id) and not is_super_admin(user_id):
        await query.message.reply_text("⛔ Нет доступа.")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    rows = get_daily_stats(today)

    await query.message.reply_text(format_daily_stats(rows, today))


async def boss_stats_current_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    if not is_boss(user_id) and not is_super_admin(user_id):
        await query.message.reply_text("⛔ Нет доступa.")
        return

    month_key = datetime.now().strftime("%Y-%m")
    rows = get_month_stats(month_key)

    await query.message.reply_text(format_month_stats(rows, month_key))


async def boss_months_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    if not is_boss(user_id) and not is_super_admin(user_id):
        await query.message.reply_text("⛔ Нет доступа.")
        return

    months = get_available_months()

    if not months:
        await query.message.reply_text("Пока нет месяцев с отчётами.")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(month, callback_data=f"boss_month_{month}")]
        for month in months
    ])

    await query.message.reply_text("Выбери месяц:", reply_markup=keyboard)


async def boss_stats_selected_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    if not is_boss(user_id) and not is_super_admin(user_id):
        await query.message.reply_text("⛔ Нет доступа.")
        return

    month_key = query.data.replace("boss_month_", "", 1)
    rows = get_month_stats(month_key)

    await query.message.reply_text(format_month_stats(rows, month_key))
