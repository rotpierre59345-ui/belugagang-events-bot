"""
BeluGANG Events - Moderation & Info Cog
"""
import discord
from discord import app_commands
from discord.ext import commands
import re
import logging
from utils.database import log_moderation, delete_user_data, init_db, get_user

logger = logging.getLogger("BeluGANG.Moderation")

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await init_db()

    # --- SLASH COMMANDS FROM VIDEO (05:06) ---

    @app_commands.command(name="info", description="Get information about BeluGANG.")
    async def info(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🐾 BeluGANG Events Bot",
            description=(
                "👋 Hi, I'm an events bot for BeluGANG!\n"
                "💸 Complete events to earn belubucks.\n"
                "💬 Talk in chat to earn XP and level up.\n"
                "❓ DM @byterand with any questions or feedback!"
            ),
            color=discord.Color.blue()
        )
        embed.set_footer(text="Playing BELUGANG")
        await interaction.response.send_message(embed=embed)

    @app_commands.group(name="data", description="Manage your personal data.")
    async def data(self, interaction: discord.Interaction):
        pass

    @data.command(name="request", description="Request your personal data.")
    async def request(self, interaction: discord.Interaction):
        data = await get_user(interaction.user.id, interaction.guild_id)
        embed = discord.Embed(title="📂 Your Data", color=discord.Color.green())
        embed.add_field(name="Belubucks", value=f"{data.get('belubucks', 0):,}")
        embed.add_field(name="Level", value=f"{data.get('level', 0)}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @data.command(name="delete", description="Delete your personal data.")
    async def delete(self, interaction: discord.Interaction):
        await delete_user_data(interaction.user.id, interaction.guild_id)
        await interaction.response.send_message("✅ Your data has been deleted.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
