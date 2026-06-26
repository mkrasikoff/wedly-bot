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


async def get_user_by_id(user_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
                "SELECT id, telegram_id, name FROM users WHERE id = ?",
                (user_id,),
        ) as cursor:
            row = await cursor.fetchone()
        return dict(row) if row else None


async def get_favorite_activity_ids(room_id: int) -> List[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
                "SELECT activity_id FROM favorites WHERE room_id = ?",
                (room_id,),
        ) as cursor:
            rows = await cursor.fetchall()
        return [int(r[0]) for r in rows]


async def save_vote(room_id: int, user_id: int, activity_id: int, session_id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO votes (room_id, user_id, activity_id, session_id, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (room_id, user_id, activity_id, session_id, datetime.utcnow().isoformat()),
        )
        await db.commit()


async def get_votes_by_session(session_id: str) -> List[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
                "SELECT * FROM votes WHERE session_id = ?", (session_id,)
        ) as cursor:
            rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_users_voted_in_session(session_id: str) -> List[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
                "SELECT DISTINCT user_id FROM votes WHERE session_id = ?", (session_id,)
        ) as cursor:
            rows = await cursor.fetchall()
        return [r[0] for r in rows]


async def save_activity_log(room_id: int, activity_id: int, session_id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO activity_log (room_id, activity_id, session_id, completed_at)
            VALUES (?, ?, ?, ?)
            """,
            (room_id, activity_id, session_id, datetime.utcnow().isoformat()),
        )
        await db.commit()


async def add_to_favorites(room_id: int, activity_id: int, added_by: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO favorites (room_id, activity_id, added_by) VALUES (?, ?, ?)",
            (room_id, activity_id, added_by),
        )
        await db.commit()


async def remove_from_favorites(room_id: int, activity_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM favorites WHERE room_id = ? AND activity_id = ?",
            (room_id, activity_id),
        )
        await db.commit()


async def get_favorites_with_titles(room_id: int) -> List[dict]:
    from bot.data.activities import get_activity_by_id
    ids = await get_favorite_activity_ids(room_id)
    result = []
    for aid in ids:
        a = get_activity_by_id(aid)
        if a:
            result.append({"activity_id": aid, "title": a["title"]})
    return result


async def update_activity_log_was_done(session_id: str, was_done: bool) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE activity_log SET was_done = ? WHERE session_id = ?",
            (1 if was_done else 0, session_id),
        )
        await db.commit()


async def update_activity_log_liked(session_id: str, liked: bool) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE activity_log SET liked = ? WHERE session_id = ?",
            (1 if liked else 0, session_id),
        )
        await db.commit()
