import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DB_PATH = os.getenv("DB_PATH", "data/report_bot.db")
DEFAULT_GREETING = os.getenv("DEFAULT_GREETING", "Добрый вечер")

if not BOT_TOKEN:
    raise RuntimeError("Не найден BOT_TOKEN в .env")
