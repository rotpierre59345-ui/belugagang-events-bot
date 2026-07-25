"""
BeluGANG Events Bot — main entry point.
Only required environment variable: DISCORD_TOKEN
"""

import asyncio
import os
import logging
import discord
from discord.ext import commands
from utils import init_db

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("belugagang")

# ── Bot setup ────────────────────────────────────────────────────────────────
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

COGS = [
    "cogs.economy",
    "cogs.levels",
    "cogs.info",
    "cogs.events",
]


class BeluGANGBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",   # prefix unused but required
            intents=intents,
            help_command=None,
        )

    async def setup_hook(self):
        # Init database
        await init_db()
        log.info("Database initialised.")

        # Load cogs
        for cog in COGS:
            await self.load_extension(cog)
            log.info(f"Loaded cog: {cog}")

        # Sync slash commands globally
        synced = await self.tree.sync()
        log.info(f"Synced {len(synced)} slash command(s).")

    async def on_ready(self):
        log.info(f"Logged in as {self.user} (ID: {self.user.id})")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="BeluGANG Events ⚡",
            )
        )

    async def on_command_error(self, ctx, error):
        log.error(f"Command error: {error}")

    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        log.error(f"App command error: {error}")
        try:
            embed = discord.Embed(
                title="BeluGANG Events — Error",
                description=f"❌ An error occurred: `{error}`",
                color=discord.Color.from_str("#ED4245"),
            )
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception:
            pass


async def main():
    bot = BeluGANGBot()
    async with bot:
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
