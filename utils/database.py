"""
Gestionnaire de base de données SQLite pour BeluGANG Events Bot.
Gère les belubucks, les niveaux et les données utilisateurs.
"""

import aiosqlite
import os
import logging

logger = logging.getLogger("BeluGANG.Database")

DB_PATH = os.getenv("DB_PATH", "data/belugagang.db")


async def init_db():
    """Initialise la base de données et crée les tables si elles n'existent pas."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER NOT NULL,
                guild_id    INTEGER NOT NULL,
                belubucks   INTEGER NOT NULL DEFAULT 0,
                xp          INTEGER NOT NULL DEFAULT 0,
                level       INTEGER NOT NULL DEFAULT 0,
                messages    INTEGER NOT NULL DEFAULT 0,
                last_work   REAL    NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, guild_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS shop_roles (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id    INTEGER NOT NULL,
                role_id     INTEGER NOT NULL,
                role_name   TEXT    NOT NULL,
                price       INTEGER NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS moderation_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id    INTEGER NOT NULL,
                user_id     INTEGER NOT NULL,
                action      TEXT    NOT NULL,
                reason      TEXT,
                timestamp   REAL    NOT NULL DEFAULT (unixepoch())
            )
        """)
        await db.commit()
    logger.info("Base de données initialisée.")


async def get_user(user_id: int, guild_id: int) -> dict:
    """Récupère ou crée un utilisateur dans la base de données."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, guild_id) VALUES (?, ?)",
            (user_id, guild_id),
        )
        await db.commit()
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id),
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else {}


async def update_user(user_id: int, guild_id: int, **kwargs):
    """Met à jour les champs d'un utilisateur."""
    if not kwargs:
        return
    fields = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [user_id, guild_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE users SET {fields} WHERE user_id = ? AND guild_id = ?",
            values,
        )
        await db.commit()


async def add_belubucks(user_id: int, guild_id: int, amount: int) -> int:
    """Ajoute (ou retire) des belubucks à un utilisateur. Retourne le nouveau solde."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, guild_id) VALUES (?, ?)",
            (user_id, guild_id),
        )
        await db.execute(
            "UPDATE users SET belubucks = MAX(0, belubucks + ?) WHERE user_id = ? AND guild_id = ?",
            (amount, user_id, guild_id),
        )
        await db.commit()
        async with db.execute(
            "SELECT belubucks FROM users WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id),
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def get_leaderboard(guild_id: int, limit: int = 10) -> list[dict]:
    """Retourne le classement des belubucks pour un serveur."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT user_id, belubucks, level, xp
            FROM users
            WHERE guild_id = ?
            ORDER BY belubucks DESC
            LIMIT ?
            """,
            (guild_id, limit),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_level_leaderboard(guild_id: int, limit: int = 10) -> list[dict]:
    """Retourne le classement des niveaux pour un serveur."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT user_id, level, xp, messages
            FROM users
            WHERE guild_id = ?
            ORDER BY xp DESC
            LIMIT ?
            """,
            (guild_id, limit),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_shop_roles(guild_id: int) -> list[dict]:
    """Retourne les rôles disponibles dans la boutique."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM shop_roles WHERE guild_id = ? ORDER BY price ASC",
            (guild_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def add_shop_role(guild_id: int, role_id: int, role_name: str, price: int):
    """Ajoute un rôle à la boutique."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO shop_roles (guild_id, role_id, role_name, price) VALUES (?, ?, ?, ?)",
            (guild_id, role_id, role_name, price),
        )
        await db.commit()


async def remove_shop_role(guild_id: int, role_id: int):
    """Supprime un rôle de la boutique."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM shop_roles WHERE guild_id = ? AND role_id = ?",
            (guild_id, role_id),
        )
        await db.commit()


async def log_moderation(guild_id: int, user_id: int, action: str, reason: str = None):
    """Enregistre une action de modération."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO moderation_log (guild_id, user_id, action, reason) VALUES (?, ?, ?, ?)",
            (guild_id, user_id, action, reason),
        )
        await db.commit()


async def delete_user_data(user_id: int, guild_id: int):
    """Supprime toutes les données d'un utilisateur (RGPD)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM users WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id),
        )
        await db.execute(
            "DELETE FROM moderation_log WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id),
        )
        await db.commit()
