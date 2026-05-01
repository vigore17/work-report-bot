from datetime import datetime


def parse_int_amount(text: str) -> int:
    cleaned = text.replace(" ", "").replace("₽", "").strip()
    if not cleaned.isdigit():
        raise ValueError("Некорректное число")
    return int(cleaned)


def get_today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def get_month_key(report_date: str) -> str:
    return report_date[:7]


def calculate_metrics(
    gross_total: int,
    retail_total: int,
    acquiring_total: int,
    cashbox_total: int,
    daily_plan: int,
    monthly_acquiring_plan: int,
    current_month_sum: int
) -> dict:
    if retail_total > gross_total:
        raise ValueError("Розница не может быть больше общей суммы")

    if acquiring_total > gross_total:
        raise ValueError("Эквайринг не может быть больше общей суммы")

    wholesale_total = gross_total - retail_total
    cash_total = gross_total - acquiring_total

    if daily_plan > 0:
        daily_plan_percent = round((gross_total / daily_plan) * 100)
    else:
        daily_plan_percent = 0

    monthly_acquiring_accumulated = current_month_sum + acquiring_total

    if monthly_acquiring_plan > 0:
        monthly_acquiring_percent = round(
            (monthly_acquiring_accumulated / monthly_acquiring_plan) * 100
        )
    else:
        monthly_acquiring_percent = 0

    return {
        "gross_total": gross_total,
        "retail_total": retail_total,
        "wholesale_total": wholesale_total,
        "acquiring_total": acquiring_total,
        "cash_total": cash_total,
        "cashbox_total": cashbox_total,
        "daily_plan": daily_plan,
        "daily_plan_percent": daily_plan_percent,
        "monthly_acquiring_plan": monthly_acquiring_plan,
        "monthly_acquiring_accumulated": monthly_acquiring_accumulated,
        "monthly_acquiring_percent": monthly_acquiring_percent,
    }
