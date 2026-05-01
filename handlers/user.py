from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from db import (
    get_store_by_id,
    get_monthly_acquiring_sum,
    save_report,
    get_last_reports_by_user,
)
from keyboards import get_stores_keyboard, get_confirm_keyboard
from utils import parse_int_amount, get_today_str, get_month_key, calculate_metrics
from formatters import format_report_message, format_preview

from states import (
    SELECTING_STORE,
    ENTERING_GROSS_TOTAL,
    ENTERING_RETAIL_TOTAL,
    ENTERING_ACQUIRING_TOTAL,
    ENTERING_CASHBOX_TOTAL,
    CONFIRMING_REPORT,
)


async def send_report_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.message.reply_text("Выбери магазин:", reply_markup=get_stores_keyboard())
    return SELECTING_STORE


async def select_store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    store_id = int(query.data.split("_")[1])
    store = get_store_by_id(store_id)

    if not store or not store["is_active"]:
        await query.message.reply_text("Магазин не найден или отключён.")
        return ConversationHandler.END

    context.user_data["store_id"] = store["id"]
    context.user_data["store_name"] = store["name"]
    context.user_data["daily_plan"] = store["daily_plan"]
    context.user_data["monthly_acquiring_plan"] = store["monthly_acquiring_plan"]
    context.user_data["report_chat_id"] = store["report_chat_id"]

    await query.message.reply_text(f"Магазин выбран: {store['name']}")
    await query.message.reply_text("Введи общую сумму за день:")
    return ENTERING_GROSS_TOTAL


async def enter_gross_total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["gross_total"] = parse_int_amount(update.message.text)
    except ValueError:
        await update.message.reply_text("Введите число без букв. Например: 75000")
        return ENTERING_GROSS_TOTAL

    await update.message.reply_text("Введи розницу:")
    return ENTERING_RETAIL_TOTAL


async def enter_retail_total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        retail_total = parse_int_amount(update.message.text)
        if retail_total > context.user_data["gross_total"]:
            raise ValueError
        context.user_data["retail_total"] = retail_total
    except ValueError:
        await update.message.reply_text("Розница не может быть больше общей суммы. Введи заново:")
        return ENTERING_RETAIL_TOTAL

    await update.message.reply_text("Введи эквайринг:")
    return ENTERING_ACQUIRING_TOTAL


async def enter_acquiring_total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        acquiring_total = parse_int_amount(update.message.text)
        if acquiring_total > context.user_data["gross_total"]:
            raise ValueError
        context.user_data["acquiring_total"] = acquiring_total
    except ValueError:
        await update.message.reply_text("Эквайринг не может быть больше общей суммы. Введи заново:")
        return ENTERING_ACQUIRING_TOTAL

    await update.message.reply_text("Введи сумму в кассе:")
    return ENTERING_CASHBOX_TOTAL


async def enter_cashbox_total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["cashbox_total"] = parse_int_amount(update.message.text)
    except ValueError:
        await update.message.reply_text("Введите число без букв. Например: 372014")
        return ENTERING_CASHBOX_TOTAL

    report_date = get_today_str()
    month_key = get_month_key(report_date)
    current_month_sum = get_monthly_acquiring_sum(context.user_data["store_id"], month_key)

    metrics = calculate_metrics(
        gross_total=context.user_data["gross_total"],
        retail_total=context.user_data["retail_total"],
        acquiring_total=context.user_data["acquiring_total"],
        cashbox_total=context.user_data["cashbox_total"],
        daily_plan=context.user_data["daily_plan"],
        monthly_acquiring_plan=context.user_data["monthly_acquiring_plan"],
        current_month_sum=current_month_sum,
    )

    context.user_data["report_date"] = report_date
    context.user_data["month_key"] = month_key
    context.user_data["metrics"] = metrics

    preview = format_preview(context.user_data["store_name"], metrics)
    await update.message.reply_text(preview, reply_markup=get_confirm_keyboard())
    return CONFIRMING_REPORT


async def confirm_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "cancel_report":
        context.user_data.clear()
        await query.message.reply_text("Отчёт отменён. Напиши /start")
        return ConversationHandler.END

    metrics = context.user_data.get("metrics")
    store_name = context.user_data.get("store_name")
    report_chat_id = context.user_data.get("report_chat_id")

    if not metrics or not store_name:
        await query.message.reply_text("Данные отчёта потерялись. Начни заново через /start")
        context.user_data.clear()
        return ConversationHandler.END

    report_text = format_report_message(store_name, metrics)

    sent_to_chat = 0
    sent_message_id = None

    if report_chat_id:
        try:
            sent_msg = await context.bot.send_message(chat_id=report_chat_id, text=report_text)
            sent_to_chat = 1
            sent_message_id = sent_msg.message_id
        except Exception as e:
            print(f"Ошибка отправки в чат: {e}")
            sent_to_chat = 0

    user = update.effective_user

    save_report(
        store_id=context.user_data["store_id"],
        user_id=user.id,
        username=user.username,
        report_date=context.user_data["report_date"],
        month_key=context.user_data["month_key"],
        gross_total=metrics["gross_total"],
        retail_total=metrics["retail_total"],
        wholesale_total=metrics["wholesale_total"],
        acquiring_total=metrics["acquiring_total"],
        cash_total=metrics["cash_total"],
        cashbox_total=metrics["cashbox_total"],
        daily_plan=metrics["daily_plan"],
        daily_plan_percent=metrics["daily_plan_percent"],
        monthly_acquiring_plan=metrics["monthly_acquiring_plan"],
        monthly_acquiring_accumulated=metrics["monthly_acquiring_accumulated"],
        sent_to_chat=sent_to_chat,
        sent_message_id=sent_message_id,
    )

    context.user_data.clear()

    if sent_to_chat:
        await query.message.reply_text("Отчёт сохранён и отправлен.")
    else:
        await query.message.reply_text("Отчёт сохранён, но в чат не отправился. Проверь chat_id.")

    return ConversationHandler.END


async def my_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    items = get_last_reports_by_user(update.effective_user.id, limit=5)

    if not items:
        await query.message.reply_text("У тебя пока нет отчётов.")
        return

    lines = ["Последние отчёты:\n"]
    for item in items:
        lines.append(
            f"{item['report_date']} | {item['store_name']} | "
            f"{item['gross_total']} | {'✅' if item['sent_to_chat'] else '⚠️'}"
        )

    await query.message.reply_text("\n".join(lines))
