import asyncio
from telegram import Bot, BotCommand
from config import BOT_TOKEN


async def main():
    bot = Bot(BOT_TOKEN)

    await bot.set_my_commands([
        BotCommand("start", "Открыть меню"),
        BotCommand("help", "Помощь"),
    ])

    print("OK: команды бота установлены")


asyncio.run(main())
