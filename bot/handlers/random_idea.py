import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.data.activities import ACTIVITIES
from bot.database.models import get_user_room, get_room_members, get_user_by_telegram_id
from bot.logger import logger

RANDOM_IDEA_INITIATOR_TEXT = (
    "Вот идея для вас 🎲\n\n"
    "✨ {title}\n\n"
    "Отправил партнёру — посмотрим, что скажет 😊"
)

RANDOM_IDEA_PARTNER_TEXT = (
    "{name} предлагает:\n\n"
    "✨ {title} 🎲\n\n"
    "Как тебе идея?"
)

RANDOM_IDEA_SOLO_TEXT = (
    "Вот идея 🎲\n\n"
    "✨ {title}"
)


async def on_random_idea(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    telegram_id = query.from_user.id

    room = context.user_data.get("room") or await get_user_room(telegram_id)
    if not room:
        await query.edit_message_text("Ты не в комнате. Напиши /start чтобы начать заново.")
        return
    context.user_data["room"] = room

    activity = random.choice(ACTIVITIES)
    logger.info("User %d got random activity: %d (%s)", telegram_id, activity["id"], activity["title"])

    back_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("↩️ Назад в комнату", callback_data="room:menu")],
    ])

    members = await get_room_members(room["room_id"])

    if len(members) > 1:
        await query.edit_message_text(
            text=RANDOM_IDEA_INITIATOR_TEXT.format(title=activity["title"]),
            reply_markup=back_keyboard,
        )
        partner = next((m for m in members if m["telegram_id"] != telegram_id), None)
        if partner:
            initiator = await get_user_by_telegram_id(telegram_id)
            initiator_name = initiator["name"] if initiator else "Кто-то"
            await context.bot.send_message(
                chat_id=partner["telegram_id"],
                text=RANDOM_IDEA_PARTNER_TEXT.format(name=initiator_name, title=activity["title"]),
                reply_markup=back_keyboard,
            )
            logger.info("Notified partner %d about random idea", partner["telegram_id"])
    else:
        await query.edit_message_text(
            text=RANDOM_IDEA_SOLO_TEXT.format(title=activity["title"]),
            reply_markup=back_keyboard,
        )
