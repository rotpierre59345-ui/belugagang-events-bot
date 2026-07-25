"""
Levels Cog — XP and level system based on chat activity.
"""

import discord
from discord import app_commands
from discord.ext import commands
import time
import logging

from utils.database import get_user, update_user, get_level_leaderboard, init_db
from utils.levels import xp_progress, xp_gain_for_message

logger = logging.getLogger("BeluGANG.Levels")

XP_COOLDOWN = 60  # seconds between two XP gains per message


class Levels(commands.Cog):
    """Level and XP system for BeluGANG."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._xp_cooldowns: dict[tuple[int, int], float] = {}

    @commands.Cog.listener()
    async def on_ready(self):
        await init_db()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        key = (message.author.id, message.guild.id)
        now = time.time()
        last = self._xp_cooldowns.get(key, 0)

        if now - last < XP_COOLDOWN:
            return

        self._xp_cooldowns[key] = now
        xp_gain = xp_gain_for_message()

        data = await get_user(message.author.id, message.guild.id)
        old_xp = data.get("xp", 0)
        old_level = data.get("level", 0)
        new_xp = old_xp + xp_gain
        new_level, _, _ = xp_progress(new_xp)

        await update_user(
            message.author.id,
            message.guild.id,
            xp=new_xp,
            level=new_level,
            messages=data.get("messages", 0) + 1,
        )

        # Level up notification
        if new_level > old_level:
            try:
                embed = discord.Embed(
                    title="🎉 Level Up!",
                    description=(
                        f"Congratulations **{message.author.display_name}**! "
                        f"You are now **Level {new_level}**! 🚀"
                    ),
                    color=discord.Color.gold(),
                )
                embed.set_thumbnail(url=message.author.display_avatar.url)
                await message.channel.send(embed=embed)
                logger.info(
                    f"{message.author} reached level {new_level} on {message.guild.name}"
                )
            except discord.Forbidden:
                pass

    # ── /level ────────────────────────────────────────────────────────────────

    @app_commands.command(name="level", description="View your level or a member's level.")
    @app_commands.describe(member="Member whose level you want to see (optional).")
    async def level(
        self,
        interaction: discord.Interaction,
        member: discord.Member = None,
    ):
        target = member or interaction.user
        data = await get_user(target.id, interaction.guild_id)
        xp = data.get("xp", 0)
        level, current_xp, needed_xp = xp_progress(xp)
        messages = data.get("messages", 0)

        # Progress bar
        bar_length = 20
        filled = int(bar_length * current_xp / needed_xp) if needed_xp > 0 else 0
        bar = "█" * filled + "░" * (bar_length - filled)

        embed = discord.Embed(
            title=f"📊 {target.display_name}'s Level",
            color=discord.Color.blurple(),
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Level", value=f"**{level}**", inline=True)
        embed.add_field(name="Total XP", value=f"**{xp:,}**", inline=True)
        embed.add_field(name="Messages", value=f"**{messages:,}**", inline=True)
        embed.add_field(
            name="Progress",
            value=f"`{bar}` {current_xp}/{needed_xp} XP",
            inline=False,
        )
        await interaction.response.send_message(embed=embed)

    # ── /rank ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="rank", description="View your rank in the XP leaderboard.")
    async def rank(self, interaction: discord.Interaction):
        await interaction.response.defer()
        rows = await get_level_leaderboard(interaction.guild_id, limit=100)
        user_rank = next(
            (i + 1 for i, r in enumerate(rows) if r["user_id"] == interaction.user.id),
            None,
        )
        data = await get_user(interaction.user.id, interaction.guild_id)
        level = data.get("level", 0)
        xp = data.get("xp", 0)

        embed = discord.Embed(
            title=f"🏅 {interaction.user.display_name}'s Rank",
            color=discord.Color.blurple(),
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="Rank", value=f"**#{user_rank or '?'}**", inline=True)
        embed.add_field(name="Level", value=f"**{level}**", inline=True)
        embed.add_field(name="Total XP", value=f"**{xp:,}**", inline=True)
        await interaction.followup.send(embed=embed)

    # ── /toplevel ─────────────────────────────────────────────────────────────

    @app_commands.command(name="toplevel", description="Server level leaderboard.")
    async def toplevel(self, interaction: discord.Interaction):
        await interaction.response.defer()
        rows = await get_level_leaderboard(interaction.guild_id, limit=10)

        embed = discord.Embed(
            title="📈 Level Leaderboard",
            color=discord.Color.blurple(),
        )
        medals = ["🥇", "🥈", "🥉"]

        if not rows:
            embed.description = "No users recorded yet."
        else:
            lines = []
            for i, row in enumerate(rows):
                member = interaction.guild.get_member(row["user_id"])
                name = member.display_name if member else f"User #{row['user_id']}"
                medal = medals[i] if i < 3 else f"`{i + 1}.`"
                lines.append(
                    f"{medal} **{name}** — Lvl **{row['level']}** ({row['xp']:,} XP)"
                )
            embed.description = "\n".join(lines)

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Levels(bot))
