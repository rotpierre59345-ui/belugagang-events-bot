"""
Moderation and Info Cog — Auto-mod, help commands, and GDPR.
"""

import discord
from discord import app_commands
from discord.ext import commands
import re
import logging

from utils.database import log_moderation, delete_user_data, init_db

logger = logging.getLogger("BeluGANG.Moderation")

# Simple regex for moderation
LINK_REGEX = re.compile(r"https?://\S+")
GIBBERISH_REGEX = re.compile(r"(.)\1{10,}")  # Characters repeated more than 10 times


class Moderation(commands.Cog):
    """Moderation and Information system for BeluGANG."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await init_db()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # Ignore moderators
        if message.author.guild_permissions.manage_messages:
            return

        content = message.content.lower()

        # Anti-links
        if LINK_REGEX.search(content):
            try:
                await message.delete()
                await log_moderation(message.guild.id, message.author.id, "Link deleted")
                await message.channel.send(
                    f"⚠️ {message.author.mention}, links are not allowed here!",
                    delete_after=5,
                )
                return
            except discord.Forbidden:
                pass

        # Anti-Gibberish
        if GIBBERISH_REGEX.search(content):
            try:
                await message.delete()
                await log_moderation(message.guild.id, message.author.id, "Gibberish deleted")
                await message.channel.send(
                    f"⚠️ {message.author.mention}, please avoid gibberish text!",
                    delete_after=5,
                )
                return
            except discord.Forbidden:
                pass

    # ── Info Commands ───────────────────────────────────────────────

    @app_commands.command(name="help", description="Show bot help information.")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🐾 BeluGANG Events Bot",
            description=(
                "👋 Hi, I'm an events bot for BeluGANG!\n"
                "💸 Complete events to earn belubucks.\n"
                "💬 Talk in chat to earn XP and level up.\n"
                "❓ DM @byterand with any questions or feedback!"
            ),
            color=discord.Color.blue(),
        )
        embed.add_field(
            name="🎮 Economy Commands",
            value="`/balance`, `/work`, `/shop`, `/buy`, `/leaderboard`",
            inline=False,
        )
        embed.add_field(
            name="📈 Level Commands",
            value="`/level`, `/rank`, `/toplevel`",
            inline=False,
        )
        embed.add_field(
            name="🛡️ Data",
            value="`/data request`, `/data delete`",
            inline=False,
        )
        embed.set_footer(text="Playing BELUGANG")
        await interaction.response.send_message(embed=embed)

    # ── Data Commands (GDPR) ───────────────────────────────────────────

    @app_commands.group(name="data", description="Manage your personal data.")
    async def data_group(self, interaction: discord.Interaction):
        pass

    @data_group.command(name="request", description="Request a summary of your data.")
    async def data_request(self, interaction: discord.Interaction):
        from utils.database import get_user

        data = await get_user(interaction.user.id, interaction.guild_id)
        if not data:
            await interaction.response.send_message(
                "❌ No data found for you.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="📂 Your BeluGANG Data",
            color=discord.Color.green(),
        )
        embed.add_field(name="User ID", value=f"`{data['user_id']}`", inline=True)
        embed.add_field(name="Belubucks", value=f"**{data['belubucks']:,}**", inline=True)
        embed.add_field(name="Level", value=f"**{data['level']}**", inline=True)
        embed.add_field(name="XP", value=f"**{data['xp']:,}**", inline=True)
        embed.add_field(name="Messages", value=f"**{data['messages']:,}**", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @data_group.command(name="delete", description="Permanently delete all your data.")
    async def data_delete(self, interaction: discord.Interaction):
        # Confirmation View
        class ConfirmDelete(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)

            @discord.ui.button(label="Confirm Deletion", style=discord.ButtonStyle.danger)
            async def confirm(self, inter: discord.Interaction, button: discord.ui.Button):
                await delete_user_data(inter.user.id, inter.guild_id)
                await inter.response.send_message(
                    "✅ All your data has been deleted from our database.",
                    ephemeral=True,
                )
                self.stop()

        embed = discord.Embed(
            title="⚠️ Warning!",
            description=(
                "Are you sure you want to delete your data?\n"
                "This includes your **belubucks**, **level**, and **XP**.\n"
                "This action is irreversible."
            ),
            color=discord.Color.red(),
        )
        await interaction.response.send_message(embed=embed, view=ConfirmDelete(), ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
