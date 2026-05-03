from config import DEFAULT_GREETING
from config import DEFAULT_GREETING


def format_report_message(store_name: str, data: dict) -> str:
    return (
        f"{DEFAULT_GREETING}\n"
        f"{store_name}:\n"
        f"Общий: {data['daily_plan']}/{data['gross_total']}/{data['daily_plan_percent']}%\n"
        f"Розница: {data['retail_total']}\n"
        f"Опт: {data['wholesale_total']}\n\n"
        f"{store_name}\n"
        f"Наличные: {data['cash_total']}\n"
        f"Эквайринг: {data['acquiring_total']}\n"
        f"Заказы ИМ: {data.get('im_orders', 0)}\n"
        f"Сумма в кассе: {data['cashbox_total']}\n\n"
        f"{data['acquiring_total']} / {data['monthly_acquiring_accumulated']} / {data['monthly_acquiring_plan']}"
    )


def format_preview(store_name: str, data: dict) -> str:
    return (
        f"Проверь отчёт:\n\n"
        f"{store_name}\n"
        f"Общий: {data['daily_plan']}/{data['gross_total']}/{data['daily_plan_percent']}%\n"
        f"Розница: {data['retail_total']}\n"
        f"Опт: {data['wholesale_total']}\n"
        f"Наличные: {data['cash_total']}\n"
        f"Эквайринг: {data['acquiring_total']}\n"
        f"Заказы ИМ: {data.get('im_orders', 0)}\n"
        f"Сумма в кассе: {data['cashbox_total']}\n"
        f"Эквайринг за месяц: {data['monthly_acquiring_accumulated']} / {data['monthly_acquiring_plan']}"
    )

def format_group_report(data: dict) -> str:
    return (
        "Добрый вечер\n"
        f"{data['store_name']}:\n"
        f"Общий {data['daily_plan']}/{data['gross_total']}/{data['daily_plan_percent']}%\n"
        f"Розница {data['retail_total']}\n"
        f"Опт {data['wholesale_total']}\n"
    )


def format_boss_report(data: dict) -> str:
    return (
        f"{data['store_name']}\n"
        f"Наличные: {data['cash_total']}\n"
        f"Эквайринг: {data['acquiring_total']}\n"
        f"Заказы ИМ: {data.get('im_orders', 0)}\n"
        f"Сумма в кассе: {data['cashbox_total']}\n\n"
        f"{data['acquiring_total']} / {data['monthly_acquiring_accumulated']} / {data['monthly_acquiring_plan']}"
    )
