from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from db import get_active_stores


def get_main_menu(is_admin: bool = False):
    buttons = [
        [InlineKeyboardButton("📊 Отправить отчёт", callback_data="send_report")],
    ]

    if is_admin:
        buttons.append([InlineKeyboardButton("🧾 Мои последние отчёты", callback_data="my_reports")])
        buttons.append([InlineKeyboardButton("🔗 Пригласить сотрудника", callback_data="create_employee_invite")])
        buttons.append([InlineKeyboardButton("🚀 Настроить новый магазин", callback_data="setup_store")])
        buttons.append([InlineKeyboardButton("👨‍💼 Админ-панель", callback_data="admin_panel")])
        buttons.append([InlineKeyboardButton("👑 Панель босса", callback_data="boss_panel")])

    return InlineKeyboardMarkup(buttons)


def get_stores_keyboard():
    stores = get_active_stores()
    buttons = [[InlineKeyboardButton(store["name"], callback_data=f"store_{store['id']}")] for store in stores]
    buttons.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_report")])
    return InlineKeyboardMarkup(buttons)


def get_confirm_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Подтвердить и отправить", callback_data="confirm_report")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_report")],
    ])


def get_admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 Обновить планы", callback_data="admin_update_plans")],
        [InlineKeyboardButton("📊 Статистика магазина", callback_data="admin_store_stats")],
        [InlineKeyboardButton("📩 Дубль полного отчёта", callback_data="admin_store_duble")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")],
    ])

def get_user_stores_keyboard(stores):
    buttons = []

    for store in stores:
        buttons.append([
            InlineKeyboardButton(store["name"], callback_data=f"store_{store['id']}")
        ])

    buttons.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_report")])

    return InlineKeyboardMarkup(buttons)
