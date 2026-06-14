import asyncio
from telegram.ext import ApplicationBuilder
from config import BOT_TOKEN
from bot.database.db import init_db
from bot.handlers.start import onboarding_handler
from bot.logger import logger


def main():
    logger.info("Starting Wedly bot...")
    asyncio.run(init_db())
    logger.info("Database initialized")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(onboarding_handler)
    logger.info("Handlers registered, polling started")
    app.run_polling()


if __name__ == "__main__":
    main()
