from telegram.ext import ApplicationBuilder, Application, CallbackQueryHandler
from config import BOT_TOKEN
from bot.database.db import init_db
from bot.handlers.start import onboarding_handler
from bot.handlers.room import on_leave, on_room_stub
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
    app.add_handler(CallbackQueryHandler(on_leave, pattern="^room:leave$"))
    app.add_handler(CallbackQueryHandler(on_room_stub, pattern="^room:"))
    logger.info("Handlers registered, polling started")
    app.run_polling()


if __name__ == "__main__":
    main()
