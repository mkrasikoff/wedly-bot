import aiosqlite
import os

DB_PATH = os.getenv("DB_PATH", "wedly.db")


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Создаём таблицы
        await db.executescript("""
                               CREATE TABLE IF NOT EXISTS users (
                                                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                                    telegram_id INTEGER UNIQUE NOT NULL,
                                                                    name TEXT NOT NULL,
                                                                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                               );

                               CREATE TABLE IF NOT EXISTS rooms (
                                                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                                    code TEXT UNIQUE NOT NULL,
                                                                    animal TEXT NOT NULL,
                                                                    emoji TEXT NOT NULL,
                                                                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                               );

                               CREATE TABLE IF NOT EXISTS room_members (
                                                                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                                           room_id INTEGER NOT NULL REFERENCES rooms(id),
                                   user_id INTEGER NOT NULL REFERENCES users(id),
                                   joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                   UNIQUE(room_id, user_id)
                                   );

                               CREATE TABLE IF NOT EXISTS activities (
                                                                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                                         title TEXT NOT NULL,
                                                                         category TEXT NOT NULL,
                                                                         is_custom BOOLEAN DEFAULT FALSE,
                                                                         room_id INTEGER REFERENCES rooms(id),
                                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                   );

                               CREATE TABLE IF NOT EXISTS mood_checks (
                                                                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                                          room_id INTEGER NOT NULL REFERENCES rooms(id),
                                   user_id INTEGER NOT NULL REFERENCES users(id),
                                   score INTEGER NOT NULL,
                                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                   );

                               CREATE TABLE IF NOT EXISTS votes (
                                                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                                    room_id INTEGER NOT NULL REFERENCES rooms(id),
                                   user_id INTEGER NOT NULL REFERENCES users(id),
                                   activity_id INTEGER NOT NULL REFERENCES activities(id),
                                   session_id TEXT NOT NULL,
                                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                   );

                               CREATE TABLE IF NOT EXISTS favorites (
                                                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                                        room_id INTEGER NOT NULL REFERENCES rooms(id),
                                   activity_id INTEGER NOT NULL REFERENCES activities(id),
                                   added_by INTEGER REFERENCES users(id),
                                   UNIQUE(room_id, activity_id)
                                   );

                               CREATE TABLE IF NOT EXISTS activity_log (
                                                                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                                           room_id INTEGER NOT NULL REFERENCES rooms(id),
                                   activity_id INTEGER NOT NULL REFERENCES activities(id),
                                   session_id TEXT NOT NULL,
                                   was_done BOOLEAN,
                                   liked BOOLEAN,
                                   completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                   );
                               """)

        # Применяем миграции (идемпотентно)
        await _run_migrations(db)

        await db.commit()


async def _run_migrations(db):
    # 001: добавить added_by в favorites
    async with db.execute("PRAGMA table_info(favorites)") as cur:
        cols = [row[1] for row in await cur.fetchall()]
    if "added_by" not in cols:
        await db.execute(
            "ALTER TABLE favorites ADD COLUMN added_by INTEGER REFERENCES users(id)"
        )
