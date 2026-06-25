from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.database.models import update_activity_log_was_done, update_activity_log_liked
from bot.data.activities import get_activity_by_id
from bot.logger import logger

FEEDBACK_START_TEXT = (
    "Кстати, как прошло с «{title}»? 🙂\n\n"
    "Удалось сделать?"
)
FEEDBACK_NOT_DONE_TEXT = "Ничего страшного — в следующий раз обязательно! 😊"
FEEDBACK_LIKED_QUESTION_TEXT = "Здорово! Понравилось? 😊"
FEEDBACK_DONE_TEXT = "Спасибо! Буду знать на будущее 🤍"


def feedback_was_done_keyboard(session_id: str, activity_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Да ✅", callback_data=f"fb:done:yes:{activity_id}:{session_id}"),
        InlineKeyboardButton("Нет 😕", callback_data=f"fb:done:no:{activity_id}:{session_id}"),
    ]])


def feedback_liked_keyboard(session_id: str, activity_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Да ❤️", callback_data=f"fb:liked:yes:{activity_id}:{session_id}"),
        InlineKeyboardButton("Не очень 😐", callback_data=f"fb:liked:no:{activity_id}:{session_id}"),
    ]])


def schedule_feedback(
        context: ContextTypes.DEFAULT_TYPE,
        session_id: str,
        room_id: int,
        activity_id: int,
        members: list,
) -> None:
    for member in members:
        job_name = f"feedback_{session_id}_{member['telegram_id']}"
        context.job_queue.run_once(
            callback=send_feedback_poll,
            when=7200,
            chat_id=member["telegram_id"],
            name=job_name,
            data={
                "session_id": session_id,
                "room_id": room_id,
                "activity_id": activity_id,
            },
        )
        logger.info("Scheduled feedback job %s for chat_id=%d", job_name, member["telegram_id"])


async def send_feedback_poll(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    data = job.data
    activity_id = data["activity_id"]
    session_id = data["session_id"]

    activity = get_activity_by_id(activity_id)
    title = activity["title"] if activity else "вашей активности"

    logger.info("Sending feedback poll for session %s to chat_id=%d", session_id, job.chat_id)
    await context.bot.send_message(
        chat_id=job.chat_id,
        text=FEEDBACK_START_TEXT.format(title=title),
        reply_markup=feedback_was_done_keyboard(session_id, activity_id),
    )


async def on_feedback_was_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    answer = parts[2]
    activity_id = int(parts[3])
    session_id = parts[4]
    was_done = answer == "yes"

    logger.info("Feedback was_done=%s for session %s from user %d", was_done, session_id, query.from_user.id)
    await update_activity_log_was_done(session_id=session_id, was_done=was_done)

    if not was_done:
        await query.edit_message_text(FEEDBACK_NOT_DONE_TEXT)
        return

    await query.edit_message_text(
        text=FEEDBACK_LIKED_QUESTION_TEXT,
        reply_markup=feedback_liked_keyboard(session_id, activity_id),
    )


async def on_feedback_liked(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    answer = parts[2]
    session_id = parts[4]
    liked = answer == "yes"

    logger.info("Feedback liked=%s for session %s from user %d", liked, session_id, query.from_user.id)
    await update_activity_log_liked(session_id=session_id, liked=liked)
    await query.edit_message_text(FEEDBACK_DONE_TEXT)
