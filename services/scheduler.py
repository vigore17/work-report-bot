import asyncio
from datetime import datetime

from db import get_connection
from formatters import format_group_report, format_boss_report


async def scheduler_loop(app):
    while True:
        try:
            now_time = datetime.now().strftime("%H:%M")
            today = datetime.now().strftime("%Y-%m-%d")

            conn = get_connection()
            cur = conn.cursor()

            cur.execute(
                """
                SELECT
                    r.*,
                    s.name AS store_name,
                    s.report_chat_id,
                    s.boss_user_id,
                    s.report_send_time
                FROM reports r
                JOIN stores s ON s.id = r.store_id
                WHERE r.sent_to_chat = 0
                  AND r.report_date = ?
                """,
                (today,)
            )

            rows = cur.fetchall()

            for row in rows:
                data = dict(row)
                send_time = data.get("report_send_time") or "19:55"

                if now_time < send_time:
                    continue

                group_message_id = None

                if data.get("report_chat_id"):
                    sent_group = await app.bot.send_message(
                        chat_id=data["report_chat_id"],
                        text=format_group_report(data),
                    )
                    group_message_id = sent_group.message_id

                if data.get("boss_user_id"):
                    try:
                        await app.bot.send_message(
                            chat_id=data["boss_user_id"],
                            text=format_boss_report(data),
                        )
                    except Exception as e:
                        print(f"Ошибка отправки отчёта боссу: {e}")

                cur.execute(
                    """
                    UPDATE reports
                    SET sent_to_chat = 1,
                        sent_message_id = ?
                    WHERE id = ?
                    """,
                    (group_message_id, data["id"])
                )

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Ошибка scheduler_loop: {e}")

        await asyncio.sleep(30)
