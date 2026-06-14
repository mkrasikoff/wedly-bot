from telegram.ext import ApplicationBuilder, Application
from config import BOT_TOKEN
from bot.database.db import init_db
from bot.handlers.start import onboarding_handler
from bot.logger import logger


async def on_startup(app: Application) -> None:
    await init_db()
    logger.info("Database initialized")


def main():
    logger.info("Starting Wedly bot...")
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(on_startup)
        .build()
    )
    app.add_handler(onboarding_handler)
    logger.info("Handlers registered, polling started")
    app.run_polling()


if __name__ == "__main__":
    main()
