from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes, ConversationHandler
from services.access import get_user_store
from db import get_acquiring_base
from services.access import get_user_stores
from keyboards import get_user_stores_keyboard
from config import TEST_REPORT_USER_ID

from db import (
    get_store_by_id,
    get_monthly_acquiring_sum,
    save_report,
    get_last_reports_by_user,
)
from keyboards import get_stores_keyboard, get_confirm_keyboard
from utils import parse_int_amount, get_today_str, get_month_key, calculate_metrics
from formatters import (
    format_report_message,
    format_preview,
    format_group_report,
    format_boss_report,
    format_full_report,
)

from states import (
    SELECTING_STORE,
    ENTERING_GROSS_TOTAL,
    ENTERING_RETAIL_TOTAL,
    ENTERING_ACQUIRING_TOTAL,
    ENTERING_CASHBOX_TOTAL,
    CONFIRMING_REPORT,
    ENTERING_IM_ORDERS,
)

async def safe_query_answer(query, label: str = ""):
    try:
        await query.answer()
    except TelegramError as e:
        print(f"Ошибка query.answer {label}: {e}")
    except Exception as e:
        print(f"Неожиданная ошибка query.answer {label}: {e}")

async def send_report_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await safe_query_answer(query, "send_report_entry")

    user_id = update.effective_user.id
    stores = get_user_stores(user_id)

    if not stores:
        await query.message.reply_text(
            "⛔ Вы не привязаны ни к одному магазину.\n"
            "Попросите директора прислать ссылку-приглашение."
        )
        return ConversationHandler.END

    context.user_data.clear()

    if len(stores) == 1:
        store = stores[0]

        context.user_data["store_id"] = store["id"]
        context.user_data["store_name"] = store["name"]
        context.user_data["daily_plan"] = store["daily_plan"]
        context.user_data["monthly_acquiring_plan"] = store["monthly_acquiring_plan"]
        context.user_data["report_chat_id"] = store["report_chat_id"]
        context.user_data["boss_user_id"] = store["boss_user_id"]
        context.user_data["report_send_time"] = store["report_send_time"]

        await query.message.reply_text(
            f"{store['name']}\nВведи общую сумму за день:"
        )

        return ENTERING_GROSS_TOTAL

    await query.message.reply_text(
        "Выбери магазин для отчёта:",
        reply_markup=get_user_stores_keyboard(stores)
    )

    return SELECTING_STORE


async def select_store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await safe_query_answer(query, "select_store")

    if query.data == "cancel_report":
        context.user_data.clear()
        await query.message.reply_text("Отчёт отменён. Напиши /start")
        return ConversationHandler.END

    store_id = int(query.data.split("_")[1])
    user_id = update.effective_user.id

    stores = get_user_stores(user_id)
    allowed_store = None

    for store in stores:
        if store["id"] == store_id:
            allowed_store = store
            break

    if not allowed_store:
        await query.message.reply_text("⛔ Нет доступа к этому магазину.")
        return ConversationHandler.END

    context.user_data["store_id"] = allowed_store["id"]
    context.user_data["store_name"] = allowed_store["name"]
    context.user_data["daily_plan"] = allowed_store["daily_plan"]
    context.user_data["monthly_acquiring_plan"] = allowed_store["monthly_acquiring_plan"]
    context.user_data["report_chat_id"] = allowed_store["report_chat_id"]
    context.user_data["boss_user_id"] = allowed_store["boss_user_id"]
    context.user_data["report_send_time"] = allowed_store["report_send_time"]

    await query.message.reply_text(
        f"{allowed_store['name']}\nВведи общую сумму за день:"
    )

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

    await update.message.reply_text("Введи количество заказов ИМ:")
    return ENTERING_IM_ORDERS

async def enter_im_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["im_orders"] = parse_int_amount(update.message.text)
    except ValueError:
        await update.message.reply_text("Введите число. Например: 1")
        return ENTERING_IM_ORDERS

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
    current_month_sum = (
    get_acquiring_base(context.user_data["store_id"], month_key)
    + get_monthly_acquiring_sum(context.user_data["store_id"], month_key)
)

    metrics = calculate_metrics(
        gross_total=context.user_data["gross_total"],
        retail_total=context.user_data["retail_total"],
        acquiring_total=context.user_data["acquiring_total"],
        cashbox_total=context.user_data["cashbox_total"],
        daily_plan=context.user_data["daily_plan"],
        monthly_acquiring_plan=context.user_data["monthly_acquiring_plan"],
        current_month_sum=current_month_sum,
    )

    metrics["im_orders"] = context.user_data.get("im_orders", 0)

    context.user_data["report_date"] = report_date
    context.user_data["month_key"] = month_key
    context.user_data["metrics"] = metrics

    preview = format_preview(context.user_data["store_name"], metrics)
    await update.message.reply_text(preview, reply_markup=get_confirm_keyboard())
    return CONFIRMING_REPORT


async def confirm_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await safe_query_answer(query, "confirm_report")

    if query.data == "cancel_report":
        context.user_data.clear()
        await query.message.reply_text("Отчёт отменён. Напиши /start")
        return ConversationHandler.END

    metrics = context.user_data.get("metrics")
    store_name = context.user_data.get("store_name")
    if not metrics or not store_name:
        await query.message.reply_text("Данные отчёта потерялись. Начни заново через /start")
        context.user_data.clear()
        return ConversationHandler.END

    user = update.effective_user

    if context.user_data.get("test_mode"):
        if not TEST_REPORT_USER_ID or user.id != TEST_REPORT_USER_ID:
            context.user_data.clear()

            await query.message.reply_text(
                "⛔ Ошибка доступа к тестовому режиму."
            )

            return ConversationHandler.END

        test_data = dict(metrics)
        test_data["store_name"] = store_name

        await query.message.reply_text(
            "🧪 TEST GROUP\n\n"
            + format_group_report(test_data)
        )

        await query.message.reply_text(
            "🧪 TEST BOSS\n\n"
            + format_boss_report(test_data)
        )

        await query.message.reply_text(
            "🧪 TEST FULL\n\n"
            + format_full_report(test_data)
        )

        context.user_data.clear()

        await query.message.reply_text(
            "✅ Тест завершён.\n\n"
            "Рабочий отчёт НЕ создан.\n"
            "В рабочие группы ничего НЕ отправлено.\n"
            "Боссу ничего НЕ отправлено."
        )

        return ConversationHandler.END

    sent_to_chat = 0
    sent_message_id = None

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
        im_orders=metrics.get("im_orders", 0),
        cash_total=metrics["cash_total"],
        cashbox_total=metrics["cashbox_total"],
        daily_plan=metrics["daily_plan"],
        daily_plan_percent=metrics["daily_plan_percent"],
        monthly_acquiring_plan=metrics["monthly_acquiring_plan"],
        monthly_acquiring_accumulated=metrics["monthly_acquiring_accumulated"],
        sent_to_chat=sent_to_chat,
        sent_message_id=sent_message_id,
    )

    report_send_time = context.user_data.get("report_send_time", "указанное время")

    context.user_data.clear()

    await query.message.reply_text(
        f"Отчёт сохранён. Он будет отправлен в {report_send_time}."
    )

    return ConversationHandler.END




async def my_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await safe_query_answer(query, "my_reports")

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

async def test_report_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    print(
        f">>> TESTREPORT ENTERED user_id={update.effective_user.id}",
        flush=True
    )
    user_id = update.effective_user.id

    if not TEST_REPORT_USER_ID or user_id != TEST_REPORT_USER_ID:
        await update.message.reply_text(
            "⛔ Тестовый режим доступен только администратору."
        )
        return ConversationHandler.END

    stores = get_user_stores(user_id)

    if not stores:
        await update.message.reply_text(
            "⛔ Нет доступных магазинов для тестирования."
        )
        return ConversationHandler.END

    context.user_data.clear()

    # Самый важный флаг.
    # По нему confirm_report поймёт,
    # что это тест и в рабочую БД писать нельзя.
    context.user_data["test_mode"] = True

    if len(stores) == 1:
        store = stores[0]

        context.user_data["store_id"] = store["id"]
        context.user_data["store_name"] = store["name"]
        context.user_data["daily_plan"] = store["daily_plan"]
        context.user_data["monthly_acquiring_plan"] = store["monthly_acquiring_plan"]
        context.user_data["report_chat_id"] = store["report_chat_id"]
        context.user_data["boss_user_id"] = store["boss_user_id"]
        context.user_data["report_send_time"] = store["report_send_time"]

        await update.message.reply_text(
            "🧪 ТЕСТОВЫЙ РЕЖИМ\n\n"
            f"Магазин: {store['name']}\n"
            "Введи общую сумму за день:"
        )

        return ENTERING_GROSS_TOTAL

    await update.message.reply_text(
        "🧪 ТЕСТОВЫЙ РЕЖИМ\n\n"
        "Выбери магазин.\n\n"
        "⚠️ Рабочие группы и босс ничего не получат.",
        reply_markup=get_user_stores_keyboard(stores)
    )

    return SELECTING_STORE

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    stores = get_user_stores(user_id)

    if not stores:
        await update.message.reply_text(
            "⛔ Вы не привязаны ни к одному магазину.\n"
            "Попросите директора прислать ссылку-приглашение."
        )
        return ConversationHandler.END

    context.user_data.clear()

    if len(stores) == 1:
        store = stores[0]

        context.user_data["store_id"] = store["id"]
        context.user_data["store_name"] = store["name"]
        context.user_data["daily_plan"] = store["daily_plan"]
        context.user_data["monthly_acquiring_plan"] = store["monthly_acquiring_plan"]
        context.user_data["report_chat_id"] = store["report_chat_id"]
        context.user_data["boss_user_id"] = store["boss_user_id"]
        context.user_data["report_send_time"] = store["report_send_time"]

        await update.message.reply_text(
            f"{store['name']}\nВведи общую сумму за день:"
        )

        return ENTERING_GROSS_TOTAL

    await update.message.reply_text(
        "Выбери магазин для отчёта:",
        reply_markup=get_user_stores_keyboard(stores)
    )

    return SELECTING_STORE
