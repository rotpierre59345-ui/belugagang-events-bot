"""
BeluGANG Events Bot
Bot Discord pour le serveur BeluGANG — gestion des événements, belubucks, niveaux et modération.
"""

import os
import asyncio
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("BeluGANG")

# Intents Discord
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

# Préfixe de commande (legacy) + slash commands
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Liste des cogs à charger
COGS = [
    "cogs.economy",
    "cogs.levels",
    "cogs.events",
    "cogs.moderation",
    "cogs.info",
]


@bot.event
async def on_ready():
    logger.info(f"Connecté en tant que {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(
        activity=discord.Game(name="BELUGANG")
    )
    try:
        synced = await bot.tree.sync()
        logger.info(f"{len(synced)} commandes slash synchronisées.")
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation des commandes : {e}")


@bot.event
async def on_guild_join(guild: discord.Guild):
    logger.info(f"Rejoint le serveur : {guild.name} (ID: {guild.id})")


async def load_cogs():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            logger.info(f"Cog chargé : {cog}")
        except Exception as e:
            logger.error(f"Impossible de charger {cog} : {e}")


async def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError("La variable d'environnement DISCORD_TOKEN est manquante.")
    async with bot:
        await load_cogs()
        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
