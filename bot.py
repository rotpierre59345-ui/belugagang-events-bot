"""
BeluGANG Events Bot — Fichier principal
Bot Discord pour le serveur BeluGANG — Events automatiques, belubucks, niveaux, modération.
"""

import os
import asyncio
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("BeluGANG")

# ── Intents Discord ────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.presences = True

# ── Instance du bot ────────────────────────────────────────────────────────────
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ── Cogs à charger ─────────────────────────────────────────────────────────────
COGS = [
    "cogs.economy",
    "cogs.levels",
    "cogs.events",
    "cogs.moderation",
    "cogs.info",
]


@bot.event
async def on_ready():
    logger.info("─── CONNEXION RÉUSSIE ───────────────────────────────")
    logger.info(f"Connecté en tant que : {bot.user} (ID : {bot.user.id})")
    logger.info(f"Présent sur {len(bot.guilds)} serveur(s).")

    await bot.change_presence(
        activity=discord.Game(name="BeluGANG Events 🎮")
    )

    try:
        synced = await bot.tree.sync()
        logger.info(f"Slash commands synchronisées : {len(synced)} commande(s).")
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation des slash commands : {e}")

    logger.info("Bot opérationnel !")


@bot.event
async def on_guild_join(guild: discord.Guild):
    logger.info(f"Nouveau serveur rejoint : {guild.name} (ID : {guild.id})")


async def load_cogs():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            logger.info(f"Cog chargé : {cog}")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du cog {cog} : {e}")


async def main():
    token = os.getenv("DISCORD_TOKEN")

    if not token:
        logger.critical(
            "ERREUR CRITIQUE : Aucun token trouvé ! "
            "Définis DISCORD_TOKEN dans les variables d'environnement (Railway / .env)."
        )
        return

    async with bot:
        await load_cogs()
        try:
            await bot.start(token)
        except discord.LoginFailure:
            logger.critical(
                "ERREUR CRITIQUE : Token invalide ! Vérifie DISCORD_TOKEN."
            )
        except Exception as e:
            logger.critical(f"ERREUR CRITIQUE inattendue : {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Arrêt du bot...")
