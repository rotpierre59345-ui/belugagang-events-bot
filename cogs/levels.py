"""
BeluGANG Events - Levels Cog
"""
import discord
from discord import app_commands
from discord.ext import commands
import logging
from utils.database import get_user, get_level_leaderboard, init_db

logger = logging.getLogger("BeluGANG.Levels")

class Levels(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await init_db()

    @app_commands.command(name="level", description="View your level or another user's level.")
    @app_commands.describe(user="The user to check.")
    async def level(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        data = await get_user(target.id, interaction.guild_id)
        await interaction.response.send_message(f"📊 **{target.display_name}** is Level **{data.get('level', 0)}**.")

    @app_commands.command(name="rank", description="View your rank.")
    async def rank(self, interaction: discord.Interaction):
        data = await get_user(interaction.user.id, interaction.guild_id)
        await interaction.response.send_message(f"🏅 Your current rank is based on Level **{data.get('level', 0)}**.")

    @app_commands.command(name="leaderboard", description="View the level leaderboard.")
    async def leaderboard(self, interaction: discord.Interaction):
        rows = await get_level_leaderboard(interaction.guild_id, limit=10)
        desc = "\n".join([f"**{i+1}.** <@{r['user_id']}> - Lvl {r['level']}" for i, r in enumerate(rows)])
        embed = discord.Embed(title="📈 Level Leaderboard", description=desc or "No data.", color=discord.Color.gold())
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Levels(bot))
