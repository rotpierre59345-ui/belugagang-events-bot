import discord
from discord import app_commands
from discord.ext import commands
from utils import get_user, xp_for_next_level

BRAND_COLOR = discord.Color.from_str("#5865F2")


class Levels(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="level", description="View your level or the level of another user")
    @app_commands.describe(user="The user whose level you want to view (optional)")
    async def level(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        data = await get_user(target.id, interaction.guild_id)

        current_level = data["level"]
        current_xp = data["xp"]
        xp_needed = xp_for_next_level(current_level)
        progress = int((current_xp / xp_needed) * 20)
        bar = "█" * progress + "░" * (20 - progress)

        embed = discord.Embed(
            title="BeluGANG Events",
            description=f"📊 **{target.display_name}'s Level**",
            color=BRAND_COLOR,
        )
        embed.add_field(name="Level", value=f"**{current_level}**", inline=True)
        embed.add_field(name="XP", value=f"**{current_xp:,}** / **{xp_needed:,}**", inline=True)
        embed.add_field(name="Progress", value=f"`{bar}` {int((current_xp / xp_needed) * 100)}%", inline=False)
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text="BeluGANG Events • Earn XP by participating in events!")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rank", description="View your level or the level of another user")
    @app_commands.describe(user="The user whose rank you want to view (optional)")
    async def rank(self, interaction: discord.Interaction, user: discord.Member = None):
        # /rank is an alias for /level
        target = user or interaction.user
        data = await get_user(target.id, interaction.guild_id)

        current_level = data["level"]
        current_xp = data["xp"]
        xp_needed = xp_for_next_level(current_level)
        progress = int((current_xp / xp_needed) * 20)
        bar = "█" * progress + "░" * (20 - progress)

        embed = discord.Embed(
            title="BeluGANG Events",
            description=f"📊 **{target.display_name}'s Rank**",
            color=BRAND_COLOR,
        )
        embed.add_field(name="Level", value=f"**{current_level}**", inline=True)
        embed.add_field(name="XP", value=f"**{current_xp:,}** / **{xp_needed:,}**", inline=True)
        embed.add_field(name="Progress", value=f"`{bar}` {int((current_xp / xp_needed) * 100)}%", inline=False)
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text="BeluGANG Events • Earn XP by participating in events!")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Levels(bot))
