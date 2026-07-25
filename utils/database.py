import aiosqlite
import os

DB_PATH = os.environ.get("DB_PATH", "belugagang.db")


async def get_db():
    return await aiosqlite.connect(DB_PATH)


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                guild_id    INTEGER NOT NULL,
                balance     INTEGER NOT NULL DEFAULT 0,
                xp          INTEGER NOT NULL DEFAULT 0,
                level       INTEGER NOT NULL DEFAULT 0,
                work_cooldown REAL NOT NULL DEFAULT 0,
                UNIQUE(user_id, guild_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS data_requests (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                guild_id    INTEGER NOT NULL,
                requested_at REAL NOT NULL
            )
        """)
        await db.commit()


async def get_user(user_id: int, guild_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id)
        ) as cursor:
            row = await cursor.fetchone()
            if row is None:
                await db.execute(
                    "INSERT OR IGNORE INTO users (user_id, guild_id) VALUES (?, ?)",
                    (user_id, guild_id)
                )
                await db.commit()
                return {
                    "user_id": user_id,
                    "guild_id": guild_id,
                    "balance": 0,
                    "xp": 0,
                    "level": 0,
                    "work_cooldown": 0.0,
                }
            return dict(row)


async def update_balance(user_id: int, guild_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, guild_id) VALUES (?, ?)",
            (user_id, guild_id)
        )
        await db.execute(
            "UPDATE users SET balance = MAX(0, balance + ?) WHERE user_id = ? AND guild_id = ?",
            (amount, user_id, guild_id)
        )
        await db.commit()


async def set_balance(user_id: int, guild_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, guild_id) VALUES (?, ?)",
            (user_id, guild_id)
        )
        await db.execute(
            "UPDATE users SET balance = ? WHERE user_id = ? AND guild_id = ?",
            (amount, user_id, guild_id)
        )
        await db.commit()


async def add_xp(user_id: int, guild_id: int, xp_amount: int) -> tuple[int, int, bool]:
    """Returns (new_xp, new_level, leveled_up)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, guild_id) VALUES (?, ?)",
            (user_id, guild_id)
        )
        async with db.execute(
            "SELECT xp, level FROM users WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id)
        ) as cursor:
            row = await cursor.fetchone()
            current_xp = row["xp"] if row else 0
            current_level = row["level"] if row else 0

        new_xp = current_xp + xp_amount
        new_level = current_level
        leveled_up = False

        xp_needed = xp_for_next_level(current_level)
        while new_xp >= xp_needed:
            new_xp -= xp_needed
            new_level += 1
            leveled_up = True
            xp_needed = xp_for_next_level(new_level)

        await db.execute(
            "UPDATE users SET xp = ?, level = ? WHERE user_id = ? AND guild_id = ?",
            (new_xp, new_level, user_id, guild_id)
        )
        await db.commit()
        return new_xp, new_level, leveled_up


def xp_for_next_level(level: int) -> int:
    return 100 + level * 50


async def set_work_cooldown(user_id: int, guild_id: int, timestamp: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, guild_id) VALUES (?, ?)",
            (user_id, guild_id)
        )
        await db.execute(
            "UPDATE users SET work_cooldown = ? WHERE user_id = ? AND guild_id = ?",
            (timestamp, user_id, guild_id)
        )
        await db.commit()


async def get_leaderboard(guild_id: int, limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT user_id, balance, level, xp FROM users WHERE guild_id = ? ORDER BY balance DESC LIMIT ?",
            (guild_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def delete_user_data(user_id: int, guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM users WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id)
        )
        await db.execute(
            "DELETE FROM data_requests WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id)
        )
        await db.commit()


async def save_data_request(user_id: int, guild_id: int, timestamp: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO data_requests (user_id, guild_id, requested_at) VALUES (?, ?, ?)",
            (user_id, guild_id, timestamp)
        )
        await db.commit()
