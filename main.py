from telegram.ext import ApplicationBuilder, Application, CallbackQueryHandler
from config import BOT_TOKEN
from bot.database.db import init_db
from bot.handlers.start import onboarding_handler
from bot.handlers.room import on_leave, on_room_stub, on_room_menu
from bot.handlers.mood import on_mood_start, on_mood_vote
from bot.handlers.vote import on_vote_done, on_vote_click, on_tiebreak
from bot.logger import logger
from telegram.ext import ContextTypes


async def on_error(_update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Unhandled exception: %s", context.error, exc_info=context.error)


async def on_startup(_app: Application) -> None:
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
    app.add_handler(CallbackQueryHandler(on_mood_start, pattern="^room:mood$"))
    app.add_handler(CallbackQueryHandler(on_mood_vote, pattern=r"^mood:\d+$"))
    app.add_handler(CallbackQueryHandler(on_vote_done, pattern=r"^vote:done:[a-f0-9\-]+$"))
    app.add_handler(CallbackQueryHandler(on_vote_click, pattern=r"^vote:\d+:[a-f0-9\-]+$"))
    app.add_handler(CallbackQueryHandler(on_tiebreak, pattern=r"^tiebreak:\d+:[a-f0-9\-]+$"))
    app.add_handler(CallbackQueryHandler(on_room_menu, pattern="^room:menu$"))
    app.add_handler(CallbackQueryHandler(on_leave, pattern="^room:leave$"))
    app.add_handler(CallbackQueryHandler(on_room_stub, pattern="^room:"))
    app.add_error_handler(on_error)
    logger.info("Handlers registered, polling started")
    app.run_polling()


if __name__ == "__main__":
    main()
