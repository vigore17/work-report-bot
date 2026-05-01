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
)
from handlers.admin import admin_entry

from states import (
    SELECTING_STORE,
    ENTERING_GROSS_TOTAL,
    ENTERING_RETAIL_TOTAL,
    ENTERING_ACQUIRING_TOTAL,
    ENTERING_CASHBOX_TOTAL,
    CONFIRMING_REPORT,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


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

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("cancel", cancel))

    app.add_handler(report_conv)
    app.add_handler(CallbackQueryHandler(my_reports, pattern="^my_reports$"))
    app.add_handler(CallbackQueryHandler(admin_entry, pattern="^admin_panel$"))

    app.run_polling()


if __name__ == "__main__":
    main()
