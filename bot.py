"""
BeluGANG Events Bot
Discord bot for the BeluGANG server — handling events, belubucks, levels, and moderation.
"""

import os
import asyncio
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("BeluGANG")

# Discord Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

# Bot instance
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Cogs to load
COGS = [
    "cogs.economy",
    "cogs.levels",
    "cogs.events",
    "cogs.moderation",
    "cogs.info",
]


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    # Status: Playing BELUGANG
    await bot.change_presence(
        activity=discord.Game(name="BELUGANG")
    )
    try:
        synced = await bot.tree.sync()
        logger.info(f"{len(synced)} slash commands synced.")
    except Exception as e:
        logger.error(f"Error syncing commands: {e}")


@bot.event
async def on_guild_join(guild: discord.Guild):
    logger.info(f"Joined server: {guild.name} (ID: {guild.id})")


async def load_cogs():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            logger.info(f"Cog loaded: {cog}")
        except Exception as e:
            logger.error(f"Failed to load {cog}: {e}")


async def main():
    token = os.getenv("DISCORD_TOKEN")
    scemer_token = os.getenv("SCEMER_TOKEN")
    
    if not token:
        raise ValueError("DISCORD_TOKEN environment variable is missing.")
    
    if scemer_token:
        logger.info("SCEMER_TOKEN detected and integrated for verification system.")
    
    async with bot:
        await load_cogs()
        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
