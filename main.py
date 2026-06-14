from telegram.ext import ApplicationBuilder
from config import BOT_TOKEN
from bot.database.db import init_db
from bot.handlers.start import onboarding_handler
import asyncio


def main():
    asyncio.get_event_loop().run_until_complete(init_db())
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(onboarding_handler)
    app.run_polling()


if __name__ == "__main__":
    main()
