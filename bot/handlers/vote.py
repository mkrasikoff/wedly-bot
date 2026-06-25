import random
from collections import Counter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.data.activities import MOOD_TO_CATEGORIES, get_activities_by_categories, get_activity_by_id
from bot.database.models import (
    get_user_room,
    get_room_members,
    get_user_by_id,
    get_favorite_activity_ids,
    save_vote,
    get_votes_by_session,
    get_users_voted_in_session,
    save_activity_log,
)
from bot.logger import logger

WINNER_TEXT = (
    "Вы сошлись во мнениях! 🎉\n\n"
    "Сегодня вы делаете:\n"
    "✨ {title}\n\n"
    "Отличный выбор 🙌"
)

WINNER_AFTER_TIE_TEXT = (
    "Решение принято! 🎲\n\n"
    "Сегодня вы делаете:\n"
    "✨ {title}"
)

TIE_DECIDER_TEXT = (
    "Похоже, вы оба правы — и это прекрасно 🤝\n"
    "Поэтому финальное слово за тобой, {name}! 🎲\n\n"
    "Что берём?"
)

TIE_OBSERVER_TEXT = (
    "У вас ничья! 🤝\n"
    "Решение за {name} — ждём её выбор..."
)


async def pick_activities(room_id: int, avg_score: int, count: int = 5) -> list:
    categories = MOOD_TO_CATEGORIES[avg_score]
    candidates = get_activities_by_categories(categories)
    if not candidates:
        return []

    favorite_ids = await get_favorite_activity_ids(room_id)
    weights = [2 if a["id"] in favorite_ids else 1 for a in candidates]

    k = min(count, len(candidates))
    pool = random.choices(candidates, weights=weights, k=k * 4)
    seen, result = set(), []
    for a in pool:
        if a["id"] not in seen:
            seen.add(a["id"])
            result.append(a)
        if len(result) == k:
            break

    if len(result) < k:
        for a in candidates:
            if a["id"] not in seen:
                result.append(a)
            if len(result) == k:
                break

    return result


def vote_keyboard(activities: list, session_id: str, voted_ids: set) -> InlineKeyboardMarkup:
    buttons = []
    for a in activities:
        prefix = "✅ " if a["id"] in voted_ids else ""
        buttons.append([InlineKeyboardButton(
            text=f"{prefix}{a['title']}",
            callback_data=f"vote:{a['id']}:{session_id}",
        )])
    buttons.append([InlineKeyboardButton("Готово ✓", callback_data=f"vote:done:{session_id}")])
    buttons.append([InlineKeyboardButton("↩️ Назад", callback_data="room:menu")])
    return InlineKeyboardMarkup(buttons)


async def show_activity_vote(source, context: ContextTypes.DEFAULT_TYPE, room: dict, activities: list, session_id: str) -> None:
    text = (
        "Вот что подходит для вашего настроения 🎯\n\n"
        "Выбери всё, что нравится — можно несколько.\n"
        "Когда определишься, нажми «Готово ✓»"
    )
    keyboard = vote_keyboard(activities, session_id, voted_ids=set())
    if isinstance(source, int):
        await context.bot.send_message(chat_id=source, text=text, reply_markup=keyboard)
    else:
        await source.edit_message_text(text=text, reply_markup=keyboard)


async def on_vote_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    activity_id = int(parts[1])
    session_id = parts[2]

    key = f"vote_ids_{session_id}"
    voted: set = context.user_data.get(key, set())
    if activity_id in voted:
        voted.discard(activity_id)
    else:
        voted.add(activity_id)
    context.user_data[key] = voted

    activities = context.bot_data.get(f"session_activities_{session_id}", [])
    await query.edit_message_reply_markup(reply_markup=vote_keyboard(activities, session_id, voted))
    logger.debug("User %d toggled activity %d in session %s", query.from_user.id, activity_id, session_id)


async def on_vote_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    session_id = query.data.split(":", 2)[2]
    telegram_id = query.from_user.id
    logger.info("User %d submitted votes in session %s", telegram_id, session_id)

    room = context.user_data.get("room") or await get_user_room(telegram_id)
    if not room:
        await query.edit_message_text("Что-то пошло не так. Напиши /start чтобы начать заново.")
        return
    context.user_data["room"] = room

    from bot.database.models import get_user_by_telegram_id
    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        await query.edit_message_text("Что-то пошло не так. Напиши /start чтобы начать заново.")
        return

    voted_ids: set = context.user_data.get(f"vote_ids_{session_id}", set())
    for activity_id in voted_ids:
        await save_vote(
            room_id=room["room_id"],
            user_id=user["id"],
            activity_id=activity_id,
            session_id=session_id,
        )

    members = await get_room_members(room["room_id"])
    voted_users = await get_users_voted_in_session(session_id)
    all_voted = {m["user_id"] for m in members} == set(voted_users)

    if len(members) == 1 or all_voted:
        await _resolve_vote(context, session_id, room)
    else:
        await query.edit_message_text(
            "Твой голос засчитан! Жду пока партнёр тоже выберет... 🕐",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад в комнату", callback_data="room:menu")],
            ]),
        )


async def on_tiebreak(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    _, activity_id_str, session_id = query.data.split(":")
    winner = get_activity_by_id(int(activity_id_str))
    telegram_id = query.from_user.id

    room = context.user_data.get("room") or await get_user_room(telegram_id)
    if not room or not winner:
        await query.edit_message_text("Что-то пошло не так. Напиши /start чтобы начать заново.")
        return

    logger.info("Tiebreak resolved: activity %d in session %s", winner["id"], session_id)
    await _announce_winner(context, session_id, room, winner, after_tie=True)


async def _resolve_vote(context: ContextTypes.DEFAULT_TYPE, session_id: str, room: dict) -> None:
    all_votes = await get_votes_by_session(session_id)
    counts = Counter(v["activity_id"] for v in all_votes)
    activities = context.bot_data.get(f"session_activities_{session_id}", [])

    if not counts:
        winner = random.choice(activities) if activities else None
        if winner:
            await _announce_winner(context, session_id, room, winner)
        return

    max_votes = max(counts.values())
    top_ids = [aid for aid, cnt in counts.items() if cnt == max_votes]

    if len(top_ids) == 1:
        winner = get_activity_by_id(top_ids[0])
        await _announce_winner(context, session_id, room, winner)
    else:
        await _handle_tie(context, session_id, room, tied_activity_ids=top_ids)


async def _handle_tie(context: ContextTypes.DEFAULT_TYPE, session_id: str, room: dict, tied_activity_ids: list) -> None:
    members = await get_room_members(room["room_id"])
    decider_member = random.choice(members)
    decider_user = await get_user_by_id(decider_member["user_id"])
    decider_name = decider_user["name"] if decider_user else "один из вас"

    tied_activities = [get_activity_by_id(aid) for aid in tied_activity_ids if get_activity_by_id(aid)]
    tie_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(a["title"], callback_data=f"tiebreak:{a['id']}:{session_id}")]
        for a in tied_activities
    ])

    for member in members:
        if member["user_id"] == decider_member["user_id"]:
            await context.bot.send_message(
                chat_id=member["telegram_id"],
                text=TIE_DECIDER_TEXT.format(name=decider_name),
                reply_markup=tie_keyboard,
            )
        else:
            await context.bot.send_message(
                chat_id=member["telegram_id"],
                text=TIE_OBSERVER_TEXT.format(name=decider_name),
            )

    logger.info("Tie in session %s, decider: %s", session_id, decider_name)


async def _announce_winner(context: ContextTypes.DEFAULT_TYPE, session_id: str, room: dict, winner: dict, after_tie: bool = False) -> None:
    members = await get_room_members(room["room_id"])
    template = WINNER_AFTER_TIE_TEXT if after_tie else WINNER_TEXT
    text = template.format(title=winner["title"])
    back_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("↩️ В меню комнаты", callback_data="room:menu")],
    ])

    for member in members:
        await context.bot.send_message(
            chat_id=member["telegram_id"],
            text=text,
            reply_markup=back_kb,
        )

    await save_activity_log(
        room_id=room["room_id"],
        activity_id=winner["id"],
        session_id=session_id,
    )
    logger.info("Winner announced: activity %d in session %s, room %s", winner["id"], session_id, room["code"])
