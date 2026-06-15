import aiosqlite
from bot.database.db import DB_PATH
from typing import Optional


async def get_user_room(telegram_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
                """
                SELECT r.id, r.code, r.animal, r.emoji
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
        return {"room_id": row["id"], "code": row["code"], "animal": row["animal"], "emoji": row["emoji"]}


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
