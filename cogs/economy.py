"""
BeluGANG Events - Economy Cog
"""
import discord
from discord import app_commands
from discord.ext import commands
import random
from utils.database import get_user, add_belubucks, init_db

class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await init_db()

    @app_commands.command(name="balance", description="Check your belubucks balance.")
    async def balance(self, interaction: discord.Interaction):
        data = await get_user(interaction.user.id, interaction.guild_id)
        await interaction.response.send_message(f"💰 You have **{data.get('belubucks', 0):,} belubucks**.")

    @app_commands.command(name="work", description="Work to earn belubucks.")
    async def work(self, interaction: discord.Interaction):
        amount = random.randint(50, 150)
        await add_belubucks(interaction.user.id, interaction.guild_id, amount)
        await interaction.response.send_message(f"💼 You worked and earned **{amount} belubucks**!")

    @app_commands.command(name="shop", description="Exchange currency for roles.")
    async def shop(self, interaction: discord.Interaction):
        await interaction.response.send_message("🛒 The shop is currently being updated with new roles!")

async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
