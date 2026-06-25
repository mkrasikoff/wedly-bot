import asyncio
import aiosqlite
import os

DB_PATH = os.environ.get("DB_PATH", "wedly.db")


async def migrate():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("PRAGMA table_info(favorites)") as cur:
            cols = [row[1] for row in await cur.fetchall()]

        if "added_by" in cols and "user_id" not in cols:
            print("Миграция не нужна — схема уже актуальна.")
            return

        if "user_id" in cols:
            print("Пересоздаём таблицу favorites с новой схемой...")
            await db.executescript("""
                                   CREATE TABLE favorites_new (
                                                                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                                  room_id INTEGER NOT NULL REFERENCES rooms(id),
                                                                  activity_id INTEGER NOT NULL REFERENCES activities(id),
                                                                  added_by INTEGER REFERENCES users(id),
                                                                  UNIQUE(room_id, activity_id)
                                   );
                                   INSERT INTO favorites_new (id, room_id, activity_id)
                                   SELECT id, room_id, activity_id FROM favorites;
                                   DROP TABLE favorites;
                                   ALTER TABLE favorites_new RENAME TO favorites;
                                   """)
            await db.commit()
            print("Готово.")
        elif "added_by" not in cols:
            print("Добавляем колонку added_by...")
            await db.execute(
                "ALTER TABLE favorites ADD COLUMN added_by INTEGER REFERENCES users(id)"
            )
            await db.commit()
            print("Готово.")


asyncio.run(migrate())
