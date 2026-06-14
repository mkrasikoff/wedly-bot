import warnings
from telegram.warnings import PTBUserWarning
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from bot.services.room_service import create_room, join_room
from bot.logger import logger

warnings.filterwarnings("ignore", category=PTBUserWarning)

CHOOSE_ACTION, ENTER_CODE = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info("/start from user %s (tg_id=%d)", user.first_name, user.id)
    keyboard = [
        [
            InlineKeyboardButton("🏠 Создать комнату", callback_data="create"),
            InlineKeyboardButton("🔑 Войти по коду", callback_data="join"),
        ]
    ]
    await update.message.reply_text(
        "Привет! Я Wedly 🐾\n\nПомогу вам с партнёром выбрать, чем заняться вместе.\n\nЧто сделаем?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CHOOSE_ACTION


async def on_create(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user = query.from_user
    logger.info("User %s (tg_id=%d) chose: create room", user.first_name, user.id)

    room = await create_room(user.id, user.first_name)

    await query.edit_message_text(
        f"{room['emoji']} Комната создана!\n\n"
        f"Твой код: `{room['code']}`\n\n"
        f"Отправь его партнёру — как только он войдёт, начнём 🎉",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def on_join_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user = query.from_user
    logger.info("User %s (tg_id=%d) chose: join room", user.first_name, user.id)

    await query.edit_message_text("Введи код комнаты:")
    return ENTER_CODE


async def on_join_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    code = update.message.text.strip().lower()
    logger.info("User %s (tg_id=%d) entered code: %s", user.first_name, user.id, code)

    result = await join_room(user.id, user.first_name, code)

    if result is None:
        await update.message.reply_text(
            "Комната с таким кодом не найдена. Проверь код и попробуй ещё раз:"
        )
        return ENTER_CODE

    await update.message.reply_text(
        f"{result['emoji']} Ты вошёл в комнату *{result['code']}*! 🎉",
        parse_mode="Markdown",
    )

    for member_tg_id in result["other_members"]:
        await context.bot.send_message(
            chat_id=member_tg_id,
            text=f"👋 *{user.first_name}* присоединился к комнате {result['emoji']}",
            parse_mode="Markdown",
        )
        logger.info("Notified member tg_id=%d about new joiner %s", member_tg_id, user.first_name)

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info("User %s (tg_id=%d) cancelled onboarding", user.first_name, user.id)
    await update.message.reply_text("Окей, до встречи! 🐾")
    return ConversationHandler.END


onboarding_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        CHOOSE_ACTION: [
            CallbackQueryHandler(on_create, pattern="^create$"),
            CallbackQueryHandler(on_join_prompt, pattern="^join$"),
        ],
        ENTER_CODE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, on_join_code),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    per_message=False,
)
