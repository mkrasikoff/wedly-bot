from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from config import BOT_TOKEN
from bot.handlers.start import start_handler
from bot.handlers.room import room_callback_handler
from bot.database.db import init_db
import asyncio

async def main():
    await init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CallbackQueryHandler(room_callback_handler))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
