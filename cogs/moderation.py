"""
Cog Modération et Info — Modération automatique, commandes d'info et RGPD.
"""

import discord
from discord import app_commands
from discord.ext import commands
import re
import logging

from utils.database import log_moderation, delete_user_data, init_db

logger = logging.getLogger("BeluGANG.Moderation")

# Regex simples pour la modération
LINK_REGEX = re.compile(r"https?://\S+")
GIBBERISH_REGEX = re.compile(r"(.)\1{10,}")  # Caractères répétés plus de 10 fois


class Moderation(commands.Cog):
    """Système de modération et informations BeluGANG."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await init_db()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # Ignorer les modérateurs
        if message.author.guild_permissions.manage_messages:
            return

        content = message.content.lower()

        # Anti-liens (sauf si autorisé)
        if LINK_REGEX.search(content):
            try:
                await message.delete()
                await log_moderation(message.guild.id, message.author.id, "Lien supprimé")
                await message.channel.send(
                    f"⚠️ {message.author.mention}, les liens ne sont pas autorisés ici !",
                    delete_after=5,
                )
                return
            except discord.Forbidden:
                pass

        # Anti-Gibberish (spam de caractères)
        if GIBBERISH_REGEX.search(content):
            try:
                await message.delete()
                await log_moderation(message.guild.id, message.author.id, "Gibberish supprimé")
                await message.channel.send(
                    f"⚠️ {message.author.mention}, évite le texte incohérent !",
                    delete_after=5,
                )
                return
            except discord.Forbidden:
                pass

    # ── Commandes d'information ───────────────────────────────────────────────

    @app_commands.command(name="info", description="Obtenir des informations sur BeluGANG.")
    async def info(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🐾 À propos de BeluGANG",
            description=(
                "BeluGANG est la communauté officielle du créateur Beluga !\n"
                "Ce bot gère les événements, l'économie des belubucks et les niveaux du serveur."
            ),
            color=discord.Color.blue(),
        )
        embed.add_field(name="Créateur", value="Beluga", inline=True)
        embed.add_field(name="Membres", value="~1,000,000", inline=True)
        embed.set_footer(text="Bot créé pour BeluGANG Events")
        await interaction.response.send_message(embed=embed)

    # ── Commandes de données (RGPD) ───────────────────────────────────────────

    @app_commands.group(name="data", description="Gérer tes données personnelles.")
    async def data_group(self, interaction: discord.Interaction):
        pass

    @data_group.command(name="request", description="Demander un résumé de tes données.")
    async def data_request(self, interaction: discord.Interaction):
        from utils.database import get_user

        data = await get_user(interaction.user.id, interaction.guild_id)
        if not data:
            await interaction.response.send_message(
                "❌ Aucune donnée trouvée pour toi.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="📂 Tes données BeluGANG",
            color=discord.Color.green(),
        )
        embed.add_field(name="User ID", value=f"`{data['user_id']}`", inline=True)
        embed.add_field(name="Belubucks", value=f"**{data['belubucks']:,}**", inline=True)
        embed.add_field(name="Niveau", value=f"**{data['level']}**", inline=True)
        embed.add_field(name="XP", value=f"**{data['xp']:,}**", inline=True)
        embed.add_field(name="Messages", value=f"**{data['messages']:,}**", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @data_group.command(name="delete", description="Supprimer définitivement toutes tes données.")
    async def data_delete(self, interaction: discord.Interaction):
        # Vue de confirmation
        class ConfirmDelete(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)

            @discord.ui.button(label="Confirmer la suppression", style=discord.ButtonStyle.danger)
            async def confirm(self, inter: discord.Interaction, button: discord.ui.Button):
                await delete_user_data(inter.user.id, inter.guild_id)
                await inter.response.send_message(
                    "✅ Toutes tes données ont été supprimées de notre base de données.",
                    ephemeral=True,
                )
                self.stop()

        embed = discord.Embed(
            title="⚠️ Attention !",
            description=(
                "Es-tu sûr de vouloir supprimer tes données ?\n"
                "Cela inclut tes **belubucks**, ton **niveau** et ton **XP**.\n"
                "Cette action est irréversible."
            ),
            color=discord.Color.red(),
        )
        await interaction.response.send_message(embed=embed, view=ConfirmDelete(), ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
