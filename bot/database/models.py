import aiosqlite
from typing import Optional, List
from datetime import datetime
from bot.database.db import DB_PATH


async def get_user_room(telegram_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
                """
                SELECT r.id as room_id, r.code, r.animal, r.emoji
                FROM rooms r
                         JOIN room_members rm ON rm.room_id = r.id
                         JOIN users u ON u.id = rm.user_id
                WHERE u.telegram_id = ?
                ORDER BY rm.joined_at DESC
                    LIMIT 1
                """,
                (telegram_id,),
        ) as cursor:
            row = await cursor.fetchone()
        if not row:
            return None
        return dict(row)


async def leave_room(telegram_id: int, room_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
                "SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            user = await cursor.fetchone()
        if not user:
            return
        await db.execute(
            "DELETE FROM room_members WHERE room_id = ? AND user_id = ?",
            (room_id, user["id"]),
        )
        await db.commit()


async def get_room_members(room_id: int) -> List[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
                """
                SELECT u.id as user_id, u.telegram_id, u.name
                FROM room_members rm
                         JOIN users u ON u.id = rm.user_id
                WHERE rm.room_id = ?
                """,
                (room_id,),
        ) as cursor:
            rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_user_by_telegram_id(telegram_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
                "SELECT id, telegram_id, name FROM users WHERE telegram_id = ?",
                (telegram_id,),
        ) as cursor:
            row = await cursor.fetchone()
        return dict(row) if row else None


async def save_mood_check(room_id: int, user_id: int, score: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO mood_checks (room_id, user_id, score, created_at) VALUES (?, ?, ?, ?)",
            (room_id, user_id, score, datetime.utcnow().isoformat()),
        )
        await db.commit()


async def get_latest_mood_check(room_id: int, user_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
                """
                SELECT * FROM mood_checks
                WHERE room_id = ? AND user_id = ?
                ORDER BY created_at DESC LIMIT 1
                """,
                (room_id, user_id),
        ) as cursor:
            row = await cursor.fetchone()
        return dict(row) if row else None
