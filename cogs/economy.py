"""
Cog Économie — Gestion des belubucks : solde, travail, boutique, classement.
"""

import discord
from discord import app_commands
from discord.ext import commands
import time
import random
import logging

from utils.database import (
    get_user,
    add_belubucks,
    update_user,
    get_leaderboard,
    get_shop_roles,
    add_shop_role,
    remove_shop_role,
    init_db,
)

logger = logging.getLogger("BeluGANG.Economy")

WORK_COOLDOWN = 3600  # 1 heure en secondes
WORK_MIN = 50
WORK_MAX = 200

WORK_MESSAGES = [
    "Tu as travaillé comme développeur Discord et gagné **{amount} belubucks** ! 💻",
    "Tu as vendu des mèmes de Beluga et gagné **{amount} belubucks** ! 🐱",
    "Tu as moderé le chat et gagné **{amount} belubucks** ! 🔨",
    "Tu as organisé un événement et gagné **{amount} belubucks** ! 🎉",
    "Tu as streamé sur Twitch et gagné **{amount} belubucks** ! 📺",
    "Tu as livré des pizzas virtuelles et gagné **{amount} belubucks** ! 🍕",
    "Tu as remporté un tournoi de jeux et gagné **{amount} belubucks** ! 🎮",
]


class Economy(commands.Cog):
    """Commandes liées à l'économie BeluGANG (belubucks)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await init_db()

    # ── /balance ──────────────────────────────────────────────────────────────

    @app_commands.command(name="balance", description="Voir ton solde de belubucks.")
    @app_commands.describe(member="Membre dont tu veux voir le solde (optionnel).")
    async def balance(
        self,
        interaction: discord.Interaction,
        member: discord.Member = None,
    ):
        target = member or interaction.user
        data = await get_user(target.id, interaction.guild_id)
        belubucks = data.get("belubucks", 0)

        embed = discord.Embed(
            title="💰 Solde BeluBucks",
            color=discord.Color.gold(),
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(
            name=target.display_name,
            value=f"**{belubucks:,} belubucks** 🪙",
            inline=False,
        )
        await interaction.response.send_message(embed=embed)

    # ── /work ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="work", description="Travailler pour gagner des belubucks.")
    async def work(self, interaction: discord.Interaction):
        data = await get_user(interaction.user.id, interaction.guild_id)
        last_work = data.get("last_work", 0)
        now = time.time()
        elapsed = now - last_work
        remaining = WORK_COOLDOWN - elapsed

        if remaining > 0:
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            embed = discord.Embed(
                title="⏳ Cooldown",
                description=f"Tu dois attendre encore **{minutes}m {seconds}s** avant de retravailler.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        amount = random.randint(WORK_MIN, WORK_MAX)
        new_balance = await add_belubucks(interaction.user.id, interaction.guild_id, amount)
        await update_user(interaction.user.id, interaction.guild_id, last_work=now)

        message = random.choice(WORK_MESSAGES).format(amount=amount)
        embed = discord.Embed(
            title="💼 Travail effectué !",
            description=message,
            color=discord.Color.green(),
        )
        embed.set_footer(text=f"Solde total : {new_balance:,} belubucks 🪙")
        await interaction.response.send_message(embed=embed)

    # ── /leaderboard ──────────────────────────────────────────────────────────

    @app_commands.command(name="leaderboard", description="Afficher le classement des belubucks.")
    async def leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer()
        rows = await get_leaderboard(interaction.guild_id, limit=10)

        embed = discord.Embed(
            title="🏆 Classement BeluBucks",
            color=discord.Color.gold(),
        )
        medals = ["🥇", "🥈", "🥉"]

        if not rows:
            embed.description = "Aucun utilisateur enregistré pour l'instant."
        else:
            lines = []
            for i, row in enumerate(rows):
                try:
                    member = interaction.guild.get_member(row["user_id"])
                    name = member.display_name if member else f"Utilisateur #{row['user_id']}"
                except Exception:
                    name = f"Utilisateur #{row['user_id']}"
                medal = medals[i] if i < 3 else f"`{i + 1}.`"
                lines.append(f"{medal} **{name}** — {row['belubucks']:,} 🪙")
            embed.description = "\n".join(lines)

        embed.set_footer(text=f"Serveur : {interaction.guild.name}")
        await interaction.followup.send(embed=embed)

    # ── /shop ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="shop", description="Voir la boutique et acheter des rôles.")
    async def shop(self, interaction: discord.Interaction):
        roles = await get_shop_roles(interaction.guild_id)

        embed = discord.Embed(
            title="🛒 Boutique BeluGANG",
            description="Utilise `/buy <rôle>` pour acheter un rôle.",
            color=discord.Color.blurple(),
        )

        if not roles:
            embed.add_field(
                name="Aucun article disponible",
                value="Un administrateur doit ajouter des rôles avec `/addshop`.",
                inline=False,
            )
        else:
            for role in roles:
                embed.add_field(
                    name=f"🎭 {role['role_name']}",
                    value=f"Prix : **{role['price']:,} belubucks** 🪙",
                    inline=True,
                )

        await interaction.response.send_message(embed=embed)

    # ── /buy ──────────────────────────────────────────────────────────────────

    @app_commands.command(name="buy", description="Acheter un rôle dans la boutique.")
    @app_commands.describe(role="Le rôle que tu veux acheter.")
    async def buy(self, interaction: discord.Interaction, role: discord.Role):
        roles = await get_shop_roles(interaction.guild_id)
        shop_role = next((r for r in roles if r["role_id"] == role.id), None)

        if not shop_role:
            await interaction.response.send_message(
                "❌ Ce rôle n'est pas disponible dans la boutique.", ephemeral=True
            )
            return

        if role in interaction.user.roles:
            await interaction.response.send_message(
                "❌ Tu possèdes déjà ce rôle.", ephemeral=True
            )
            return

        data = await get_user(interaction.user.id, interaction.guild_id)
        balance = data.get("belubucks", 0)
        price = shop_role["price"]

        if balance < price:
            await interaction.response.send_message(
                f"❌ Solde insuffisant. Il te faut **{price:,} belubucks** mais tu n'en as que **{balance:,}**.",
                ephemeral=True,
            )
            return

        new_balance = await add_belubucks(interaction.user.id, interaction.guild_id, -price)
        try:
            await interaction.user.add_roles(role, reason="Achat boutique BeluGANG")
        except discord.Forbidden:
            await add_belubucks(interaction.user.id, interaction.guild_id, price)
            await interaction.response.send_message(
                "❌ Je n'ai pas la permission d'attribuer ce rôle.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="✅ Achat réussi !",
            description=f"Tu as obtenu le rôle **{role.name}** pour **{price:,} belubucks** 🪙",
            color=discord.Color.green(),
        )
        embed.set_footer(text=f"Solde restant : {new_balance:,} belubucks")
        await interaction.response.send_message(embed=embed)

    # ── /addshop (admin) ──────────────────────────────────────────────────────

    @app_commands.command(name="addshop", description="[Admin] Ajouter un rôle à la boutique.")
    @app_commands.describe(role="Le rôle à ajouter.", price="Prix en belubucks.")
    @app_commands.default_permissions(administrator=True)
    async def addshop(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
        price: int,
    ):
        if price <= 0:
            await interaction.response.send_message("❌ Le prix doit être positif.", ephemeral=True)
            return
        await add_shop_role(interaction.guild_id, role.id, role.name, price)
        await interaction.response.send_message(
            f"✅ Rôle **{role.name}** ajouté à la boutique pour **{price:,} belubucks**.",
            ephemeral=True,
        )

    # ── /removeshop (admin) ───────────────────────────────────────────────────

    @app_commands.command(name="removeshop", description="[Admin] Retirer un rôle de la boutique.")
    @app_commands.describe(role="Le rôle à retirer.")
    @app_commands.default_permissions(administrator=True)
    async def removeshop(self, interaction: discord.Interaction, role: discord.Role):
        await remove_shop_role(interaction.guild_id, role.id)
        await interaction.response.send_message(
            f"✅ Rôle **{role.name}** retiré de la boutique.", ephemeral=True
        )

    # ── /give (admin) ─────────────────────────────────────────────────────────

    @app_commands.command(name="give", description="[Admin] Donner des belubucks à un membre.")
    @app_commands.describe(member="Le membre cible.", amount="Montant à donner.")
    @app_commands.default_permissions(administrator=True)
    async def give(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        amount: int,
    ):
        if amount <= 0:
            await interaction.response.send_message("❌ Le montant doit être positif.", ephemeral=True)
            return
        new_balance = await add_belubucks(member.id, interaction.guild_id, amount)
        await interaction.response.send_message(
            f"✅ **{amount:,} belubucks** donnés à **{member.display_name}**. Nouveau solde : **{new_balance:,}** 🪙",
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
