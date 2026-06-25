from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.data.activities import ACTIVITIES, get_activity_by_id
from bot.database.models import (
    get_user_room,
    get_favorite_activity_ids,
    get_favorites_with_titles,
    add_to_favorites,
    remove_from_favorites,
    get_user_by_telegram_id,
)
from bot.logger import logger

PAGE_SIZE = 8

FAVORITES_EMPTY_TEXT = (
    "Здесь пока пусто 🌱\n\n"
    "Загляни в «📋 Все идеи» и добавь то, что нравится —\n"
    "оно будет приоритетным при следующем подборе!"
)


async def on_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    telegram_id = query.from_user.id

    room = context.user_data.get("room") or await get_user_room(telegram_id)
    if not room:
        await query.edit_message_text("Ты не в комнате. Напиши /start чтобы начать заново.")
        return
    context.user_data["room"] = room

    favorites = await get_favorites_with_titles(room["room_id"])

    if not favorites:
        await query.edit_message_text(
            FAVORITES_EMPTY_TEXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 Посмотреть все идеи", callback_data="room:list:0")],
                [InlineKeyboardButton("↩️ Назад в комнату", callback_data="room:menu")],
            ]),
        )
        return

    buttons = [
        [InlineKeyboardButton(f["title"], callback_data=f"fav:card:{f['activity_id']}")]
        for f in favorites
    ]
    buttons.append([InlineKeyboardButton("↩️ Назад в комнату", callback_data="room:menu")])

    logger.info("User %d viewing favorites for room %s (%d items)", telegram_id, room["code"], len(favorites))
    await query.edit_message_text(
        f"❤️ Избранное вашей комнаты — {len(favorites)} идей",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def on_all_activities(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    telegram_id = query.from_user.id

    room = context.user_data.get("room") or await get_user_room(telegram_id)
    if not room:
        await query.edit_message_text("Ты не в комнате. Напиши /start чтобы начать заново.")
        return
    context.user_data["room"] = room

    parts = query.data.split(":")
    page = int(parts[2]) if len(parts) > 2 else 0

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    page_items = ACTIVITIES[start:end]

    buttons = [
        [InlineKeyboardButton(a["title"], callback_data=f"activity:{a['id']}:{page}")]
        for a in page_items
    ]

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("← Назад", callback_data=f"room:list:{page - 1}"))
    if end < len(ACTIVITIES):
        nav.append(InlineKeyboardButton("Ещё →", callback_data=f"room:list:{page + 1}"))
    if nav:
        buttons.append(nav)

    buttons.append([InlineKeyboardButton("↩️ В меню комнаты", callback_data="room:menu")])

    await query.edit_message_text(
        "📋 Все идеи\n\nНажми на активность, чтобы посмотреть подробнее и добавить в избранное.",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def on_activity_card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    telegram_id = query.from_user.id

    parts = query.data.split(":")
    activity_id = int(parts[1])
    page = int(parts[2]) if len(parts) > 2 else 0

    room = context.user_data.get("room") or await get_user_room(telegram_id)
    if not room:
        await query.edit_message_text("Ты не в комнате. Напиши /start чтобы начать заново.")
        return
    context.user_data["room"] = room

    activity = get_activity_by_id(activity_id)
    if not activity:
        await query.answer("Активность не найдена", show_alert=True)
        return

    favorite_ids = await get_favorite_activity_ids(room["room_id"])
    is_fav = activity_id in favorite_ids

    fav_label = "💔 Убрать из избранного" if is_fav else "❤️ В избранное"
    await query.edit_message_text(
        text=f"✨ {activity['title']}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(fav_label, callback_data=f"fav:toggle:{activity_id}:{page}")],
            [InlineKeyboardButton("↩️ Назад к списку", callback_data=f"room:list:{page}")],
        ]),
    )


async def on_fav_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    telegram_id = query.from_user.id

    parts = query.data.split(":")
    activity_id = int(parts[2])
    page = int(parts[3]) if len(parts) > 3 else 0

    room = context.user_data.get("room") or await get_user_room(telegram_id)
    if not room:
        await query.answer("Ты не в комнате.", show_alert=True)
        return
    context.user_data["room"] = room

    user = await get_user_by_telegram_id(telegram_id)
    favorite_ids = await get_favorite_activity_ids(room["room_id"])

    if activity_id in favorite_ids:
        await remove_from_favorites(room["room_id"], activity_id)
        new_label = "❤️ В избранное"
        await query.answer("Убрано из избранного", show_alert=False)
        logger.info("User %d removed activity %d from favorites in room %s", telegram_id, activity_id, room["code"])
    else:
        added_by = user["id"] if user else None
        await add_to_favorites(room["room_id"], activity_id, added_by)
        new_label = "💔 Убрать из избранного"
        await query.answer("Добавлено в избранное ❤️", show_alert=False)
        logger.info("User %d added activity %d to favorites in room %s", telegram_id, activity_id, room["code"])

    await query.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(new_label, callback_data=f"fav:toggle:{activity_id}:{page}")],
            [InlineKeyboardButton("↩️ Назад к списку", callback_data=f"room:list:{page}")],
        ]),
    )


async def on_fav_card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    telegram_id = query.from_user.id
    activity_id = int(query.data.split(":")[2])

    room = context.user_data.get("room") or await get_user_room(telegram_id)
    if not room:
        await query.edit_message_text("Ты не в комнате. Напиши /start чтобы начать заново.")
        return
    context.user_data["room"] = room

    activity = get_activity_by_id(activity_id)
    if not activity:
        await query.answer("Активность не найдена", show_alert=True)
        return

    await query.edit_message_text(
        text=f"✨ {activity['title']}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💔 Убрать из избранного", callback_data=f"fav:remove:{activity_id}")],
            [InlineKeyboardButton("↩️ Назад к избранному", callback_data="room:favorites")],
        ]),
    )


async def on_fav_remove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    telegram_id = query.from_user.id
    activity_id = int(query.data.split(":")[2])

    room = context.user_data.get("room") or await get_user_room(telegram_id)
    if not room:
        await query.answer("Ты не в комнате.", show_alert=True)
        return
    context.user_data["room"] = room

    await remove_from_favorites(room["room_id"], activity_id)
    await query.answer("Убрано из избранного", show_alert=False)
    logger.info("User %d removed activity %d from favorites (fav screen)", telegram_id, activity_id)

    await on_favorites(update, context)
