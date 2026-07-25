"""
BeluGANG Events Bot (Main Instance)
"""
import os
import asyncio
import logging
import discord
from discord.ext import commands
from bot import bot, load_cogs

logger = logging.getLogger("BeluGANG.Main")

async def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.critical("DISCORD_TOKEN missing!")
        return
    async with bot:
        await load_cogs()
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
