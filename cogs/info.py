import discord
from discord import app_commands
from discord.ext import commands
import time
from utils import delete_user_data, save_data_request, get_user

BRAND_COLOR = discord.Color.from_str("#5865F2")
SUCCESS_COLOR = discord.Color.from_str("#57F287")
ERROR_COLOR = discord.Color.from_str("#ED4245")
WARNING_COLOR = discord.Color.from_str("#FEE75C")


class Info(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="info", description="Get help and information for BeluGANG Events")
    async def info(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="BeluGANG Events",
            description="Get help and information for BeluGANG Events",
            color=BRAND_COLOR,
        )
        embed.add_field(
            name="📋 Commands",
            value=(
                "`/balance` — View your balance or another user's balance\n"
                "`/work` — Work to earn belubucks (1h cooldown)\n"
                "`/leaderboard` — See the top earners on the server\n"
                "`/level` — View your level and XP progress\n"
                "`/rank` — Same as /level\n"
                "`/shop` — Browse rewards available for belubucks\n"
                "`/info` — Show this help message\n"
                "`/data request` — Request a copy of your stored data\n"
                "`/data delete` — Delete all your personal data"
            ),
            inline=False,
        )
        embed.add_field(
            name="⚡ Auto Events",
            value=(
                "Events are automatically triggered in the server!\n"
                "• **Flash Event** — Be the first to click GO!\n"
                "• **Flag Event** — Guess the correct country flag\n"
                "• **Collect Event** — Collect belubucks before they disappear!\n"
                "• **Rock Paper Scissors** — Beat the bot!"
            ),
            inline=False,
        )
        embed.add_field(
            name="💰 Currency",
            value="The server currency is **belubucks**. Earn them by working and winning events!",
            inline=False,
        )
        embed.set_footer(text="BeluGANG Events • As a thank you for supporting BeluGANG!")
        await interaction.response.send_message(embed=embed)


class DataGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="data", description="Manage your personal data stored by BeluGANG Events")

    @app_commands.command(name="delete", description="Deletes all personal data stored by BeluGANG Events")
    async def data_delete(self, interaction: discord.Interaction):
        # Confirmation view
        view = ConfirmDeleteView(interaction.user.id)
        embed = discord.Embed(
            title="BeluGANG Events — Data Deletion",
            description=(
                "⚠️ **Are you sure you want to delete all your data?**\n\n"
                "This will permanently delete:\n"
                "• Your belubucks balance\n"
                "• Your level and XP\n"
                "• All stored personal data\n\n"
                "**This action cannot be undone.**"
            ),
            color=WARNING_COLOR,
        )
        embed.set_footer(text="BeluGANG Events")
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="request", description="Submit a request for your personal data")
    async def data_request(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = await get_user(interaction.user.id, interaction.guild_id)
        await save_data_request(interaction.user.id, interaction.guild_id, time.time())

        embed = discord.Embed(
            title="BeluGANG Events — Your Data",
            description="Here is all the personal data we store about you:",
            color=BRAND_COLOR,
        )
        embed.add_field(name="User ID", value=str(interaction.user.id), inline=True)
        embed.add_field(name="Guild ID", value=str(interaction.guild_id), inline=True)
        embed.add_field(name="Belubucks Balance", value=f"{data['balance']:,}", inline=True)
        embed.add_field(name="Level", value=str(data["level"]), inline=True)
        embed.add_field(name="XP", value=str(data["xp"]), inline=True)
        embed.add_field(
            name="Data Policy",
            value="Your data is only used to power BeluGANG Events features. Use `/data delete` to remove it.",
            inline=False,
        )
        embed.set_footer(text="BeluGANG Events")
        await interaction.followup.send(embed=embed, ephemeral=True)


class ConfirmDeleteView(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=30)
        self.author_id = author_id

    @discord.ui.button(label="Yes, delete my data", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This is not your button!", ephemeral=True)
            return
        await delete_user_data(interaction.user.id, interaction.guild_id)
        embed = discord.Embed(
            title="BeluGANG Events — Data Deleted",
            description="✅ All your personal data has been permanently deleted.",
            color=discord.Color.from_str("#57F287"),
        )
        embed.set_footer(text="BeluGANG Events")
        self.stop()
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This is not your button!", ephemeral=True)
            return
        embed = discord.Embed(
            title="BeluGANG Events",
            description="❌ Data deletion cancelled.",
            color=discord.Color.from_str("#ED4245"),
        )
        embed.set_footer(text="BeluGANG Events")
        self.stop()
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)


class InfoCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data_group = DataGroup()
        bot.tree.add_command(self.data_group)

    @app_commands.command(name="info", description="Get help and information for BeluGANG Events")
    async def info(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="BeluGANG Events",
            description="Get help and information for BeluGANG Events",
            color=BRAND_COLOR,
        )
        embed.add_field(
            name="📋 Commands",
            value=(
                "`/balance` — View your balance or another user's balance\n"
                "`/work` — Work to earn belubucks (1h cooldown)\n"
                "`/leaderboard` — See the top earners on the server\n"
                "`/level` — View your level and XP progress\n"
                "`/rank` — Same as /level\n"
                "`/shop` — Browse rewards available for belubucks\n"
                "`/info` — Show this help message\n"
                "`/data request` — Request a copy of your stored data\n"
                "`/data delete` — Delete all your personal data"
            ),
            inline=False,
        )
        embed.add_field(
            name="⚡ Auto Events",
            value=(
                "Events are automatically triggered in the server!\n"
                "• **Flash Event** — Be the first to click GO!\n"
                "• **Flag Event** — Guess the correct country flag\n"
                "• **Collect Event** — Collect belubucks before they disappear!\n"
                "• **Rock Paper Scissors** — Beat the bot!"
            ),
            inline=False,
        )
        embed.add_field(
            name="💰 Currency",
            value="The server currency is **belubucks**. Earn them by working and winning events!",
            inline=False,
        )
        embed.set_footer(text="BeluGANG Events • As a thank you for supporting BeluGANG!")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(InfoCog(bot))
