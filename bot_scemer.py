"""
Scemer Bot (Secondary Instance)
"""
import os
import asyncio
import logging
import discord
from discord.ext import commands
from bot import load_cogs

# Create a separate bot instance for Scemer
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
scemer_bot = commands.Bot(command_prefix="?", intents=intents, help_command=None)

logger = logging.getLogger("BeluGANG.Scemer")

@scemer_bot.event
async def on_ready():
    logger.info(f"Scemer Bot logged in as {scemer_bot.user}")
    await scemer_bot.change_presence(activity=discord.Game(name="BELUGANG"))

async def main():
    token = os.getenv("SCEMER_TOKEN")
    if not token:
        logger.critical("SCEMER_TOKEN missing!")
        return
    async with scemer_bot:
        # We don't load all cogs for Scemer to keep it light, or load specific ones if needed
        await scemer_bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
