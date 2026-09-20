import asyncio
import traceback
from datetime import datetime

from db import (
    get_connection,
    get_due_store_stats_subscriptions,
    mark_store_stats_subscription_sent,
)
from formatters import (
    format_group_report,
    format_boss_report,
    format_full_report,
)
from services.store_stats import format_store_smart_stats


async def safe_send(bot, chat_id, text, label):
    if not chat_id:
        print(f"{label}: SKIP no chat_id", flush=True)
        return None

    try:
        msg = await bot.send_message(chat_id=chat_id, text=text)
        print(f"{label}: OK message_id={msg.message_id}", flush=True)
        return msg
    except Exception as e:
        print(f"{label}: ERROR {e}", flush=True)
        traceback.print_exc()
        return None


async def scheduler_loop(app):
    print("SCHEDULER LOOP RUNNING", flush=True)

    while True:
        conn = None

        try:
            now = datetime.now()
            now_time = now.strftime("%H:%M")
            today = now.strftime("%Y-%m-%d")

            conn = get_connection()
            cur = conn.cursor()

            cur.execute(
                """
                SELECT
                    r.*,
                    s.name AS store_name,
                    s.report_chat_id,
                    s.boss_user_id,
                    s.full_report_chat_id,
                    s.report_send_time
                FROM reports r
                JOIN stores s ON s.id = r.store_id
                WHERE r.sent_to_chat = 0
                  AND r.report_date = ?
                ORDER BY r.id ASC
                """,
                (today,)
            )

            rows = cur.fetchall()

            if rows:
                print(
                    f"SCHEDULER: found unsent reports={len(rows)} today={today} now={now_time}",
                    flush=True
                )

            for row in rows:
                data = dict(row)
                report_id = data["id"]
                store_name = data["store_name"]
                send_time = data.get("report_send_time") or "19:55"

                print(
                    f"SCHEDULER: check report_id={report_id} store={store_name} send_time={send_time} now={now_time}",
                    flush=True
                )

                if now_time < send_time:
                    print(
                        f"SCHEDULER: skip report_id={report_id}, time not reached",
                        flush=True
                    )
                    continue

                group_msg = await safe_send(
                    app.bot,
                    data.get("report_chat_id"),
                    format_group_report(data),
                    f"SCHEDULER report_id={report_id} GROUP",
                )

                if not group_msg:
                    print(
                        f"SCHEDULER: report_id={report_id} group failed, NOT marking sent",
                        flush=True
                    )
                    continue

                cur.execute(
                    """
                    UPDATE reports
                    SET sent_to_chat = 1,
                        sent_message_id = ?
                    WHERE id = ?
                    """,
                    (group_msg.message_id, report_id)
                )
                conn.commit()

                print(
                    f"SCHEDULER: report_id={report_id} marked sent",
                    flush=True
                )

                await safe_send(
                    app.bot,
                    data.get("boss_user_id"),
                    format_boss_report(data),
                    f"SCHEDULER report_id={report_id} BOSS",
                )

                await safe_send(
                    app.bot,
                    data.get("full_report_chat_id"),
                    format_full_report(data),
                    f"SCHEDULER report_id={report_id} FULL",
                )

                print(
                    f"SCHEDULER: report_id={report_id} done",
                    flush=True
                )

            due_subscriptions = get_due_store_stats_subscriptions(now_time, today)

            for sub in due_subscriptions:
                try:
                    text = format_store_smart_stats(sub["store_id"])

                    msg = await safe_send(
                        app.bot,
                        sub["target_chat_id"],
                        text,
                        f"SCHEDULER stats_sub_id={sub['id']}",
                    )

                    if msg:
                        mark_store_stats_subscription_sent(sub["id"], today)

                except Exception as e:
                    print(f"Ошибка отправки статистики магазина: {e}", flush=True)
                    traceback.print_exc()

            if conn:
                conn.close()

        except Exception as e:
            print(f"Ошибка scheduler_loop: {e}", flush=True)
            traceback.print_exc()

            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

        await asyncio.sleep(30)
