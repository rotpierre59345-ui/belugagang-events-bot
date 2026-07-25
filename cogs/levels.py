"""
Cog Niveaux — Système d'XP et de niveaux basé sur l'activité dans le chat.
"""

import discord
from discord import app_commands
from discord.ext import commands
import time
import logging

from utils.database import get_user, update_user, get_level_leaderboard, init_db
from utils.levels import xp_progress, xp_gain_for_message

logger = logging.getLogger("BeluGANG.Levels")

XP_COOLDOWN = 60  # secondes entre deux gains d'XP par message


class Levels(commands.Cog):
    """Système de niveaux et d'XP pour BeluGANG."""

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

        # Notification de montée de niveau
        if new_level > old_level:
            try:
                embed = discord.Embed(
                    title="🎉 Level Up !",
                    description=(
                        f"Félicitations **{message.author.display_name}** ! "
                        f"Tu es maintenant **Niveau {new_level}** ! 🚀"
                    ),
                    color=discord.Color.gold(),
                )
                embed.set_thumbnail(url=message.author.display_avatar.url)
                await message.channel.send(embed=embed)
                logger.info(
                    f"{message.author} a atteint le niveau {new_level} sur {message.guild.name}"
                )
            except discord.Forbidden:
                pass

    # ── /level ────────────────────────────────────────────────────────────────

    @app_commands.command(name="level", description="Voir ton niveau ou celui d'un membre.")
    @app_commands.describe(member="Membre dont tu veux voir le niveau (optionnel).")
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

        # Barre de progression
        bar_length = 20
        filled = int(bar_length * current_xp / needed_xp) if needed_xp > 0 else 0
        bar = "█" * filled + "░" * (bar_length - filled)

        embed = discord.Embed(
            title=f"📊 Niveau de {target.display_name}",
            color=discord.Color.blurple(),
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Niveau", value=f"**{level}**", inline=True)
        embed.add_field(name="XP Total", value=f"**{xp:,}**", inline=True)
        embed.add_field(name="Messages", value=f"**{messages:,}**", inline=True)
        embed.add_field(
            name="Progression",
            value=f"`{bar}` {current_xp}/{needed_xp} XP",
            inline=False,
        )
        await interaction.response.send_message(embed=embed)

    # ── /rank ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="rank", description="Voir ton rang dans le classement XP.")
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
            title=f"🏅 Rang de {interaction.user.display_name}",
            color=discord.Color.blurple(),
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="Rang", value=f"**#{user_rank or '?'}**", inline=True)
        embed.add_field(name="Niveau", value=f"**{level}**", inline=True)
        embed.add_field(name="XP Total", value=f"**{xp:,}**", inline=True)
        await interaction.followup.send(embed=embed)

    # ── /toplevel ─────────────────────────────────────────────────────────────

    @app_commands.command(name="toplevel", description="Classement des niveaux du serveur.")
    async def toplevel(self, interaction: discord.Interaction):
        await interaction.response.defer()
        rows = await get_level_leaderboard(interaction.guild_id, limit=10)

        embed = discord.Embed(
            title="📈 Classement des Niveaux",
            color=discord.Color.blurple(),
        )
        medals = ["🥇", "🥈", "🥉"]

        if not rows:
            embed.description = "Aucun utilisateur enregistré pour l'instant."
        else:
            lines = []
            for i, row in enumerate(rows):
                member = interaction.guild.get_member(row["user_id"])
                name = member.display_name if member else f"Utilisateur #{row['user_id']}"
                medal = medals[i] if i < 3 else f"`{i + 1}.`"
                lines.append(
                    f"{medal} **{name}** — Niv. **{row['level']}** ({row['xp']:,} XP)"
                )
            embed.description = "\n".join(lines)

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Levels(bot))
