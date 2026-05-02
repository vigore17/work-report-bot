import logging

from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN
from db import init_db
from handlers.common import start, cancel, help_command
from handlers.user import (
    send_report_entry,
    select_store,
    enter_gross_total,
    enter_retail_total,
    enter_acquiring_total,
    enter_cashbox_total,
    confirm_report,
    my_reports,
    enter_im_orders,
)
from handlers.admin import admin_entry
from handlers.onboarding import (
    setup_store_entry,
    setup_store_name,
    setup_daily_plan,
    setup_monthly_acquiring_plan,
    setup_acquiring_base,
    setup_report_time,
    setup_report_chat_id,
    setup_boss_id,
    confirm_setup_store,
    create_employee_invite,
)
from states import (
    SELECTING_STORE,
    ENTERING_GROSS_TOTAL,
    ENTERING_RETAIL_TOTAL,
    ENTERING_ACQUIRING_TOTAL,
    ENTERING_IM_ORDERS,
    ENTERING_CASHBOX_TOTAL,
    CONFIRMING_REPORT,
    SETUP_STORE_NAME,
    SETUP_DAILY_PLAN,
    SETUP_MONTHLY_ACQUIRING_PLAN,
    SETUP_ACQUIRING_BASE,
    SETUP_REPORT_TIME,
    SETUP_REPORT_CHAT_ID,
    SETUP_BOSS_ID,
    SETUP_CONFIRM,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


async def error_handler(update, context):
    logger.error("Exception while handling an update:", exc_info=context.error)


def main():
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    report_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(send_report_entry, pattern="^send_report$")],
        states={
            SELECTING_STORE: [
                CallbackQueryHandler(select_store, pattern=r"^store_\d+$"),
                CallbackQueryHandler(confirm_report, pattern="^cancel_report$"),
            ],
            ENTERING_GROSS_TOTAL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_gross_total)
            ],
            ENTERING_RETAIL_TOTAL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_retail_total)
            ],
            ENTERING_ACQUIRING_TOTAL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_acquiring_total)
            ],
            ENTERING_IM_ORDERS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_im_orders)
            ],
            ENTERING_CASHBOX_TOTAL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_cashbox_total)
            ],
            CONFIRMING_REPORT: [
                CallbackQueryHandler(confirm_report, pattern="^(confirm_report|cancel_report)$")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    setup_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(setup_store_entry, pattern="^setup_store$")],
        states={
            SETUP_STORE_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, setup_store_name)
            ],
            SETUP_DAILY_PLAN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, setup_daily_plan)
            ],
            SETUP_MONTHLY_ACQUIRING_PLAN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, setup_monthly_acquiring_plan)
            ],
            SETUP_ACQUIRING_BASE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, setup_acquiring_base)
            ],
            SETUP_REPORT_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, setup_report_time)
            ],
            SETUP_REPORT_CHAT_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, setup_report_chat_id)
            ],
            SETUP_BOSS_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, setup_boss_id)
            ],
            SETUP_CONFIRM: [
                CallbackQueryHandler(
                    confirm_setup_store,
                    pattern="^(confirm_setup_store|cancel_setup_store)$",
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("cancel", cancel))

    app.add_handler(setup_conv)
    app.add_handler(report_conv)

    app.add_handler(CallbackQueryHandler(create_employee_invite, pattern="^create_employee_invite$"))
    app.add_handler(CallbackQueryHandler(my_reports, pattern="^my_reports$"))
    app.add_handler(CallbackQueryHandler(admin_entry, pattern="^admin_panel$"))

    app.add_error_handler(error_handler)

    app.run_polling()


if __name__ == "__main__":
    main()
