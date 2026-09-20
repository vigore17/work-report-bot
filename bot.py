import logging
import asyncio
from services.scheduler import scheduler_loop

from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN, TEST_REPORT_USER_ID
from db import init_db
from handlers.common import start, cancel, help_command
from handlers.user import (
    send_report_entry,
    report_command,
    select_store,
    test_report_command,
    enter_gross_total,
    enter_retail_total,
    enter_acquiring_total,
    enter_cashbox_total,
    confirm_report,
    my_reports,
    enter_im_orders,
)
from handlers.admin import (
    admin_entry,
    back_to_main,
    admin_update_plans_entry,
    admin_select_plan_store,
    admin_save_plans,
    admin_store_stats_entry,
    admin_select_stats_store,
    admin_full_report_chat_entry,
    admin_select_full_report_store,
    admin_save_full_report_chat,
    admin_stats_subscription_entry,
    admin_select_stats_subscription_store,
    admin_stats_subscription_target,
    admin_stats_subscription_chat_id,
    admin_stats_subscription_period,
    admin_stats_subscription_time,
)
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
    select_store_for_employee_invite,
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
    ADMIN_SET_PLANS_STORE,
    ADMIN_SET_PLANS_VALUE,
    SET_FULL_REPORT_CHAT_STORE,
    SET_FULL_REPORT_CHAT_VALUE,
    STATS_SUB_STORE,
    STATS_SUB_TARGET,
    STATS_SUB_CHAT_ID,
    STATS_SUB_PERIOD,
    STATS_SUB_TIME,
)

from handlers.boss import (
    boss_panel,
    boss_stats_today,
    boss_stats_current_month,
    boss_months_list,
    boss_stats_selected_month,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

logging.getLogger("httpx").setLevel(logging.WARNING)


async def error_handler(update, context):
    logger.error("Exception while handling an update:", exc_info=context.error)

async def webhook_guard(app):
    while True:
        try:
            info = await app.bot.get_webhook_info()

            if info.url:
                bad_url = info.url

                logger.error(
                    "UNEXPECTED WEBHOOK DETECTED: %s",
                    bad_url,
                )

                await app.bot.delete_webhook(
                    drop_pending_updates=False
                )

                logger.warning(
                    "UNEXPECTED WEBHOOK DELETED"
                )

                if TEST_REPORT_USER_ID:
                    try:
                        await app.bot.send_message(
                            chat_id=TEST_REPORT_USER_ID,
                            text=(
                                "⚠️ Work Report Bot обнаружил "
                                "посторонний webhook и автоматически "
                                "удалил его.\n\n"
                                f"Webhook: {bad_url}"
                            ),
                        )
                    except Exception:
                        logger.exception(
                            "Failed to send webhook alert"
                        )

        except Exception:
            logger.exception("Webhook guard error")

        await asyncio.sleep(60)


async def post_init(app):
    info = await app.bot.get_webhook_info()

    if info.url:
        logger.warning(
            "Webhook found on startup: %s. Deleting.",
            info.url,
        )

        await app.bot.delete_webhook(
            drop_pending_updates=False
        )

    print("SCHEDULER STARTED", flush=True)

    asyncio.create_task(scheduler_loop(app))
    asyncio.create_task(webhook_guard(app))

def main():
    init_db()

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .build()
    )

    report_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(send_report_entry, pattern="^send_report$"),
            CommandHandler("report", report_command),
            CommandHandler("testreport", test_report_command),
        ],
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
                CallbackQueryHandler(
                    confirm_report,
                    pattern="^(confirm_report|cancel_report)$"
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
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

    admin_plans_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                admin_update_plans_entry,
                pattern="^admin_update_plans$"
            )
        ],
        states={
            ADMIN_SET_PLANS_STORE: [
                CallbackQueryHandler(
                    admin_select_plan_store,
                    pattern=r"^(admin_plan_store_\d+|admin_cancel)$"
                )
            ],
            ADMIN_SET_PLANS_VALUE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    admin_save_plans
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    full_report_chat_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                admin_full_report_chat_entry,
                pattern="^admin_store_duble$"
            )
        ],
        states={
            SET_FULL_REPORT_CHAT_STORE: [
                CallbackQueryHandler(
                    admin_select_full_report_store,
                    pattern=r"^(admin_full_report_store_\d+|admin_cancel)$"
                )
            ],
            SET_FULL_REPORT_CHAT_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_save_full_report_chat)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    stats_subscription_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                admin_stats_subscription_entry,
                pattern="^admin_stats_subscription$"
            )
        ],
        states={
            STATS_SUB_STORE: [
                CallbackQueryHandler(
                    admin_select_stats_subscription_store,
                    pattern=r"^(admin_stats_sub_store_\d+|admin_cancel)$"
                )
            ],
            STATS_SUB_TARGET: [
                CallbackQueryHandler(
                    admin_stats_subscription_target,
                    pattern=r"^(stats_sub_target_private|stats_sub_target_group|admin_cancel)$"
                )
            ],
            STATS_SUB_CHAT_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_stats_subscription_chat_id)
            ],
            STATS_SUB_PERIOD: [
                CallbackQueryHandler(
                    admin_stats_subscription_period,
                    pattern=r"^(stats_sub_period_1|stats_sub_period_2|stats_sub_period_3|admin_cancel)$"
                )
            ],
            STATS_SUB_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_stats_subscription_time)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    app.add_handler(setup_conv)
    app.add_handler(report_conv)
    
    app.add_handler(admin_plans_conv)
    app.add_handler(full_report_chat_conv)
    app.add_handler(stats_subscription_conv)

    app.add_handler(CallbackQueryHandler(admin_store_stats_entry, pattern="^admin_store_stats$"))
    app.add_handler(CallbackQueryHandler(admin_select_stats_store, pattern=r"^(admin_stats_store_\d+|admin_cancel)$"))
    app.add_handler(CallbackQueryHandler(back_to_main, pattern="^back_to_main$"))

    app.add_handler(CallbackQueryHandler(create_employee_invite, pattern="^create_employee_invite$"))
    app.add_handler(CallbackQueryHandler(my_reports, pattern="^my_reports$"))
    app.add_handler(CallbackQueryHandler(admin_entry, pattern="^admin_panel$"))
    app.add_handler(CallbackQueryHandler(boss_panel, pattern="^boss_panel$"))
    app.add_handler(CallbackQueryHandler(boss_stats_today, pattern="^boss_stats_today$"))
    app.add_handler(CallbackQueryHandler(boss_stats_current_month, pattern="^boss_stats_month_current$"))
    app.add_handler(CallbackQueryHandler(boss_months_list, pattern="^boss_stats_months_list$"))
    app.add_handler(CallbackQueryHandler(boss_stats_selected_month, pattern=r"^boss_month_\d{4}-\d{2}$"))
    app.add_handler(CallbackQueryHandler(select_store_for_employee_invite, pattern=r"^invite_store_\d+$"))

    app.add_error_handler(error_handler)

    app.run_polling(
        allowed_updates=["message", "callback_query"]
    )


if __name__ == "__main__":
    main()
