from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.database.models import get_user_room, leave_room
from bot.logger import logger


async def show_room_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    room = context.user_data.get("room")
    user = update.effective_user
    logger.info("Showing room menu to user %s (tg_id=%d), room=%s", user.first_name, user.id, room["code"])

    keyboard = [
        [InlineKeyboardButton("🎭 Что делаем?", callback_data="room:mood")],
        [InlineKeyboardButton("🎲 Случайная идея", callback_data="room:random")],
        [InlineKeyboardButton("❤️ Избранное", callback_data="room:favorites")],
        [InlineKeyboardButton("📋 Все идеи", callback_data="room:list")],
        [InlineKeyboardButton("🚪 Выйти из комнаты", callback_data="room:leave")],
    ]
    text = f"{room['emoji']} Комната *{room['code']}*\n\nЧто будем делать?"

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )


async def on_room_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = query.from_user

    room = context.user_data.get("room") or await get_user_room(user.id)
    if not room:
        await query.edit_message_text("Ты не в комнате. Напиши /start 🐾")
        return
    context.user_data["room"] = room
    await show_room_menu(update, context)


async def on_leave(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = query.from_user

    room = context.user_data.get("room") or await get_user_room(user.id)
    if not room:
        logger.warning("User %s (tg_id=%d) tried to leave but has no room", user.first_name, user.id)
        await query.edit_message_text("Ты уже не в комнате. Напиши /start 🐾")
        return

    await leave_room(user.id, room["room_id"])
    context.user_data.pop("room", None)

    logger.info("User %s (tg_id=%d) left room %s", user.first_name, user.id, room["code"])
    await query.edit_message_text(
        "Ты вышел из комнаты. Напиши /start чтобы создать новую или войти в другую 🐾"
    )


async def on_room_stub(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🚧 Этот раздел скоро появится!")
