import calendar
from datetime import date

from db import get_store_smart_month_stats


def format_store_smart_stats(store_id: int, month_key: str | None = None) -> str:
    today = date.today()

    if month_key is None:
        month_key = today.strftime("%Y-%m")

    stats = get_store_smart_month_stats(store_id, month_key)

    if not stats:
        return "Статистика не найдена."

    store_name = stats["store_name"]
    monthly_sales_plan = stats["monthly_sales_plan"] or 0

    reports_count = stats["reports_count"] or 0
    gross_total = stats["gross_total"] or 0
    retail_total = stats["retail_total"] or 0
    wholesale_total = stats["wholesale_total"] or 0
    acquiring_total = stats["acquiring_total"] or 0
    im_orders = stats["im_orders"] or 0
    cash_total = stats["cash_total"] or 0

    days_in_month = calendar.monthrange(today.year, today.month)[1]
    days_passed = today.day
    days_left = max(days_in_month - days_passed, 0)

    fact_month_percent = round((gross_total / monthly_sales_plan) * 100) if monthly_sales_plan else 0

    plan_to_today = round((monthly_sales_plan / days_in_month) * days_passed) if monthly_sales_plan else 0
    pace_percent = round((gross_total / plan_to_today) * 100) if plan_to_today else 0

    projected_month = round((gross_total / days_passed) * days_in_month) if days_passed else 0

    remaining = max(monthly_sales_plan - gross_total, 0)

    if days_left > 0:
        needed_per_day = round(remaining / days_left)
    else:
        needed_per_day = remaining

    diff = gross_total - plan_to_today

    if monthly_sales_plan <= 0:
        status = "⚠️ Месячный план не задан."
    elif diff >= 0:
        status = f"🚀 Идёте с опережением графика на {diff} ₽."
    else:
        status = f"⚠️ Отставание от графика: {abs(diff)} ₽."

    return (
        f"📊 Статистика магазина за {month_key}\n\n"
        f"🏬 {store_name}\n"
        f"Отчётов: {reports_count}\n\n"
        f"🎯 План месяца: {monthly_sales_plan}\n"
        f"💰 Сделано: {gross_total}\n"
        f"📈 Факт выполнения месяца: {fact_month_percent}%\n\n"
        f"📍 План к текущему дню: {plan_to_today}\n"
        f"⚡ Темп к текущему дню: {pace_percent}%\n"
        f"🔮 Прогноз месяца: {projected_month}\n\n"
        f"⏳ Осталось до плана: {remaining}\n"
        f"📅 Дней прошло: {days_passed} из {days_in_month}\n"
        f"📆 Дней осталось: {days_left}\n"
        f"🔥 Нужно делать в день: {needed_per_day}\n\n"
        f"{status}\n\n"
        f"Дополнительно:\n"
        f"Розница: {retail_total}\n"
        f"Опт: {wholesale_total}\n"
        f"Эквайринг: {acquiring_total}\n"
        f"Заказы ИМ: {im_orders}\n"
        f"Наличные: {cash_total}"
    )
