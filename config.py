import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DB_PATH = os.getenv("DB_PATH", "data/report_bot.db")
DEFAULT_GREETING = os.getenv("DEFAULT_GREETING", "Добрый вечер")

if not BOT_TOKEN:
    raise RuntimeError("Не найден BOT_TOKEN в .env")

DEFAULT_REPORT_CHAT_ID = os.getenv("DEFAULT_REPORT_CHAT_ID")
DEFAULT_BOSS_USER_ID = os.getenv("DEFAULT_BOSS_USER_ID")


def parse_optional_int(value):
    if value is None or value == "" or value == "0":
        return None
    return int(value)


DEFAULT_REPORT_CHAT_ID = parse_optional_int(DEFAULT_REPORT_CHAT_ID)
DEFAULT_BOSS_USER_ID = parse_optional_int(DEFAULT_BOSS_USER_ID)
