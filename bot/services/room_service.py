from __future__ import annotations

import random
import string
import aiosqlite
from bot.data.animals import ANIMALS
from bot.database.db import DB_PATH


def generate_room_code() -> tuple[str, str, str]:
    animal = random.choice(ANIMALS)
    digits = "".join(random.choices(string.digits, k=4))
    code = f"{animal['name']}-{digits}"
    return code, animal["name"], animal["emoji"]


async def create_room(telegram_id: int, name: str) -> dict:
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

        code, animal, emoji = generate_room_code()
        for _ in range(10):
            async with db.execute(
                    "SELECT id FROM rooms WHERE code = ?", (code,)
            ) as cursor:
                existing = await cursor.fetchone()
            if not existing:
                break
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
            "INSERT INTO room_members (room_id, user_id) VALUES (?, ?)",
            (room_id, user_id),
        )
        await db.commit()

        return {"code": code, "animal": animal, "emoji": emoji, "room_id": room_id}


async def join_room(telegram_id: int, name: str, code: str) -> dict | None:
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

        return {
            "code": room["code"],
            "animal": room["animal"],
            "emoji": room["emoji"],
            "room_id": room_id,
            "other_members": [m["telegram_id"] for m in members],
        }
