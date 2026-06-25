import math
from uuid import uuid4
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.database.models import (
    get_user_room,
    get_room_members,
    get_user_by_telegram_id,
    save_mood_check,
    get_latest_mood_check,
)
from bot.data.activities import MOOD_TO_CATEGORIES, get_activities_by_categories
from bot.logger import logger

MOOD_QUESTION_TEXT = (
    "Как вы себя чувствуете прямо сейчас? 🌡️\n\n"
    "Выберите, и я подберу что-то подходящее для вас обоих."
)

WAITING_FOR_PARTNER_TEXT = (
    "Отлично, твой голос засчитан! ✅\n\n"
    "Жду пока {name} тоже выберет настроение...\n"
    "Как только он/она ответит — сразу подберу идеи 🙂"
)


def mood_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("😴 1 — Совсем нет сил", callback_data="mood:1")],
        [InlineKeyboardButton("😌 2 — Хочется чего-то тихого", callback_data="mood:2")],
        [InlineKeyboardButton("🙂 3 — Средне, можно что-нибудь", callback_data="mood:3")],
        [InlineKeyboardButton("😊 4 — Неплохо, готов к активности", callback_data="mood:4")],
        [InlineKeyboardButton("🔥 5 — Полон энергии!", callback_data="mood:5")],
        [InlineKeyboardButton("↩️ Назад", callback_data="room:menu")],
    ])


async def on_mood_start(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    logger.info("User %d opened mood poll", query.from_user.id)
    await query.edit_message_text(text=MOOD_QUESTION_TEXT, reply_markup=mood_keyboard())


async def on_mood_vote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    telegram_id = query.from_user.id
    score = int(query.data.split(":")[1])
    logger.info("User %d voted mood: %d", telegram_id, score)

    room = context.user_data.get("room") or await get_user_room(telegram_id)
    if not room:
        await query.edit_message_text("Ты не в комнате. Напиши /start чтобы начать заново.")
        return
    context.user_data["room"] = room

    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        await query.edit_message_text("Что-то пошло не так. Напиши /start.")
        return

    await save_mood_check(room_id=room["room_id"], user_id=user["id"], score=score)

    members = await get_room_members(room["room_id"])

    if len(members) == 1:
        logger.info("Single user in room %s, starting matching immediately", room["code"])
        await _start_matching(query, context, room, avg_score=score)
        return

    partner = next((m for m in members if m["telegram_id"] != telegram_id), None)
    partner_check = await get_latest_mood_check(room_id=room["room_id"], user_id=partner["user_id"])

    if partner_check is None:
        logger.info("Waiting for partner in room %s", room["code"])
        context.bot_data[f"waiting_{room['room_id']}"] = query.message.chat_id
        await query.edit_message_text(
            text=WAITING_FOR_PARTNER_TEXT.format(name=partner["name"]),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад в комнату", callback_data="room:menu")],
            ]),
        )
        return

    my_check = await get_latest_mood_check(room_id=room["room_id"], user_id=user["id"])
    avg_score = max(1, math.floor((my_check["score"] + partner_check["score"]) / 2))
    logger.info("Both voted in room %s, avg_score=%d", room["code"], avg_score)

    await _start_matching(query, context, room, avg_score=avg_score)

    waiting_chat_id = context.bot_data.pop(f"waiting_{room['room_id']}", None)
    if waiting_chat_id:
        await context.bot.send_message(
            chat_id=waiting_chat_id,
            text="Партнёр ответил — подбираю идеи для вас обоих! 🔍\n\n🚧 Голосование появится совсем скоро.",
        )


async def _start_matching(query, context: ContextTypes.DEFAULT_TYPE, room: dict, avg_score: int) -> None:
    session_id = str(uuid4())
    categories = MOOD_TO_CATEGORIES[avg_score]
    activities = get_activities_by_categories(categories)

    context.bot_data[f"session_activities_{session_id}"] = activities
    context.bot_data[f"current_session_{room['room_id']}"] = session_id

    logger.info(
        "Session %s started for room %s, avg_score=%d, categories=%s, activities=%d",
        session_id, room["code"], avg_score, categories, len(activities),
    )

    await query.edit_message_text(
        f"Настроение учтено! Средний балл: {avg_score} 🎯\n\n"
        f"Категории: {', '.join(categories)}\n\n"
        "🚧 Голосование за активности появится в следующем обновлении!"
    )
