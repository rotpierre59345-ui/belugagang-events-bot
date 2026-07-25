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
intents.presences = True

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
    logger.info(f"--- CONNECTION SUCCESSFUL ---")
    logger.info(f"Logged in as: {bot.user} (ID: {bot.user.id})")
    
    # Set status: Playing BELUGANG
    await bot.change_presence(
        activity=discord.Game(name="BELUGANG")
    )
    
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} slash commands successfully.")
    except Exception as e:
        logger.error(f"Failed to sync slash commands: {e}")
    
    logger.info(f"Bot is now fully operational and online!")


@bot.event
async def on_guild_join(guild: discord.Guild):
    logger.info(f"Joined new server: {guild.name} (ID: {guild.id})")


async def load_cogs():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            logger.info(f"Loaded extension: {cog}")
        except Exception as e:
            logger.error(f"Failed to load extension {cog}: {e}")


async def main():
    # Priority to SCEMER_TOKEN if provided by user, otherwise fallback to DISCORD_TOKEN
    scemer_token = os.getenv("SCEMER_TOKEN")
    discord_token = os.getenv("DISCORD_TOKEN")
    
    token = scemer_token if scemer_token else discord_token
    
    if not token:
        logger.critical("CRITICAL ERROR: No token found! Please set DISCORD_TOKEN or SCEMER_TOKEN in Railway variables.")
        return

    if scemer_token:
        logger.info("Using SCEMER_TOKEN for connection...")
    else:
        logger.info("Using default DISCORD_TOKEN for connection...")

    async with bot:
        await load_cogs()
        try:
            await bot.start(token)
        except discord.LoginFailure:
            logger.critical("CRITICAL ERROR: The provided token is invalid! Please check your token in Railway.")
        except Exception as e:
            logger.critical(f"CRITICAL ERROR: An unexpected error occurred: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutting down...")
