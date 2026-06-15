import random
import string
import aiosqlite
from bot.data.animals import ANIMALS
from bot.database.db import DB_PATH
from bot.logger import logger
from typing import Optional, Tuple


def generate_room_code() -> Tuple[str, str, str]:
    animal = random.choice(ANIMALS)
    digits = "".join(random.choices(string.digits, k=4))
    code = f"{animal['name']}-{digits}"
    return code, animal["name"], animal["emoji"]


async def create_room(telegram_id: int, name: str) -> dict:
    logger.info("Creating room for user %s (tg_id=%d)", name, telegram_id)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            "INSERT OR IGNORE INTO users (telegram_id, name) VALUES (?, ?)",
            (telegram_id, name),
        )
        async with db.execute(
                "SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            user = await cursor.fetchone()
        user_id = user["id"]
        logger.debug("User resolved: id=%d, name=%s", user_id, name)

        # Выходим из всех предыдущих комнат
        await db.execute(
            "DELETE FROM room_members WHERE user_id = ?",
            (user_id,),
        )

        code, animal, emoji = generate_room_code()
        for _ in range(10):
            async with db.execute(
                    "SELECT id FROM rooms WHERE code = ?", (code,)
            ) as cursor:
                existing = await cursor.fetchone()
            if not existing:
                break
            logger.debug("Code collision on %s, retrying...", code)
            code, animal, emoji = generate_room_code()

        await db.execute(
            "INSERT INTO rooms (code, animal, emoji) VALUES (?, ?, ?)",
            (code, animal, emoji),
        )
        async with db.execute(
                "SELECT id FROM rooms WHERE code = ?", (code,)
        ) as cursor:
            room = await cursor.fetchone()
        room_id = room["id"]

        await db.execute(
            "DELETE FROM room_members WHERE user_id = ?",
            (user_id,),
        )

        await db.execute(
            "INSERT INTO room_members (room_id, user_id) VALUES (?, ?)",
            (room_id, user_id),
        )
        await db.commit()

    logger.info("Room created: code=%s, animal=%s, room_id=%d", code, animal, room_id)
    return {"code": code, "animal": animal, "emoji": emoji, "room_id": room_id}


async def join_room(telegram_id: int, name: str, code: str) -> Optional[dict]:
    logger.info("User %s (tg_id=%d) attempting to join room: %s", name, telegram_id, code)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            "INSERT OR IGNORE INTO users (telegram_id, name) VALUES (?, ?)",
            (telegram_id, name),
        )
        async with db.execute(
                "SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            user = await cursor.fetchone()
        user_id = user["id"]

        async with db.execute(
                "SELECT * FROM rooms WHERE code = ?", (code.lower(),)
        ) as cursor:
            room = await cursor.fetchone()

        if not room:
            logger.warning("Room not found: code=%s, requested by tg_id=%d", code, telegram_id)
            return None

        room_id = room["id"]

        await db.execute(
            "INSERT OR IGNORE INTO room_members (room_id, user_id) VALUES (?, ?)",
            (room_id, user_id),
        )
        await db.commit()

        async with db.execute(
                """
                SELECT u.telegram_id FROM room_members rm
                                              JOIN users u ON u.id = rm.user_id
                WHERE rm.room_id = ? AND u.telegram_id != ?
                """,
                (room_id, telegram_id),
        ) as cursor:
            members = await cursor.fetchall()

    other = [m["telegram_id"] for m in members]
    logger.info("User %s joined room %s, notifying %d member(s)", name, code, len(other))
    return {
        "code": room["code"],
        "animal": room["animal"],
        "emoji": room["emoji"],
        "room_id": room_id,
        "other_members": other,
    }
