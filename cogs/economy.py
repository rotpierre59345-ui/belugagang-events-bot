"""
Economy Cog — Belubucks management: balance, work, shop, leaderboard.
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

WORK_COOLDOWN = 3600  # 1 hour in seconds
WORK_MIN = 50
WORK_MAX = 200

WORK_MESSAGES = [
    "You worked as a Discord developer and earned **{amount} belubucks**! 💻",
    "You sold some Beluga memes and earned **{amount} belubucks**! 🐱",
    "You moderated the chat and earned **{amount} belubucks**! 🔨",
    "You organized an event and earned **{amount} belubucks**! 🎉",
    "You streamed on Twitch and earned **{amount} belubucks**! 📺",
    "You delivered virtual pizzas and earned **{amount} belubucks**! 🍕",
    "You won a gaming tournament and earned **{amount} belubucks**! 🎮",
]


class Economy(commands.Cog):
    """Commands related to the BeluGANG economy (belubucks)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await init_db()

    # ── /balance ──────────────────────────────────────────────────────────────

    @app_commands.command(name="balance", description="Check your belubucks balance.")
    @app_commands.describe(member="Member whose balance you want to see (optional).")
    async def balance(
        self,
        interaction: discord.Interaction,
        member: discord.Member = None,
    ):
        target = member or interaction.user
        data = await get_user(target.id, interaction.guild_id)
        belubucks = data.get("belubucks", 0)

        embed = discord.Embed(
            title="💰 BeluBucks Balance",
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

    @app_commands.command(name="work", description="Work to earn belubucks.")
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
                description=f"You need to wait **{minutes}m {seconds}s** before working again.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        amount = random.randint(WORK_MIN, WORK_MAX)
        new_balance = await add_belubucks(interaction.user.id, interaction.guild_id, amount)
        await update_user(interaction.user.id, interaction.guild_id, last_work=now)

        message = random.choice(WORK_MESSAGES).format(amount=amount)
        embed = discord.Embed(
            title="💼 Work Completed!",
            description=message,
            color=discord.Color.green(),
        )
        embed.set_footer(text=f"Total Balance: {new_balance:,} belubucks 🪙")
        await interaction.response.send_message(embed=embed)

    # ── /leaderboard ──────────────────────────────────────────────────────────

    @app_commands.command(name="richlist", description="Display the belubucks leaderboard.")
    async def richlist(self, interaction: discord.Interaction):
        await interaction.response.defer()
        rows = await get_leaderboard(interaction.guild_id, limit=10)

        embed = discord.Embed(
            title="🏆 BeluBucks Leaderboard",
            color=discord.Color.gold(),
        )
        medals = ["🥇", "🥈", "🥉"]

        if not rows:
            embed.description = "No users recorded yet."
        else:
            lines = []
            for i, row in enumerate(rows):
                try:
                    member = interaction.guild.get_member(row["user_id"])
                    name = member.display_name if member else f"User #{row['user_id']}"
                except Exception:
                    name = f"User #{row['user_id']}"
                medal = medals[i] if i < 3 else f"`{i + 1}.`"
                lines.append(f"{medal} **{name}** — {row['belubucks']:,} 🪙")
            embed.description = "\n".join(lines)

        embed.set_footer(text=f"Server: {interaction.guild.name}")
        await interaction.followup.send(embed=embed)

    # ── /shop ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="shop", description="View the shop and buy roles.")
    async def shop(self, interaction: discord.Interaction):
        roles = await get_shop_roles(interaction.guild_id)

        embed = discord.Embed(
            title="🛒 BeluGANG Shop",
            description="Use `/buy <role>` to purchase a role.",
            color=discord.Color.blurple(),
        )

        if not roles:
            embed.add_field(
                name="No items available",
                value="An admin needs to add roles using `/addshop`.",
                inline=False,
            )
        else:
            for role in roles:
                embed.add_field(
                    name=f"🎭 {role['role_name']}",
                    value=f"Price: **{role['price']:,} belubucks** 🪙",
                    inline=True,
                )

        await interaction.response.send_message(embed=embed)

    # ── /buy ──────────────────────────────────────────────────────────────────

    @app_commands.command(name="buy", description="Buy a role from the shop.")
    @app_commands.describe(role="The role you want to buy.")
    async def buy(self, interaction: discord.Interaction, role: discord.Role):
        roles = await get_shop_roles(interaction.guild_id)
        shop_role = next((r for r in roles if r["role_id"] == role.id), None)

        if not shop_role:
            await interaction.response.send_message(
                "❌ This role is not available in the shop.", ephemeral=True
            )
            return

        if role in interaction.user.roles:
            await interaction.response.send_message(
                "❌ You already have this role.", ephemeral=True
            )
            return

        data = await get_user(interaction.user.id, interaction.guild_id)
        balance = data.get("belubucks", 0)
        price = shop_role["price"]

        if balance < price:
            await interaction.response.send_message(
                f"❌ Insufficient balance. You need **{price:,} belubucks** but you only have **{balance:,}**.",
                ephemeral=True,
            )
            return

        new_balance = await add_belubucks(interaction.user.id, interaction.guild_id, -price)
        try:
            await interaction.user.add_roles(role, reason="BeluGANG Shop Purchase")
        except discord.Forbidden:
            await add_belubucks(interaction.user.id, interaction.guild_id, price)
            await interaction.response.send_message(
                "❌ I don't have permission to assign this role.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="✅ Purchase Successful!",
            description=f"You obtained the **{role.name}** role for **{price:,} belubucks** 🪙",
            color=discord.Color.green(),
        )
        embed.set_footer(text=f"Remaining Balance: {new_balance:,} belubucks")
        await interaction.response.send_message(embed=embed)

    # ── /addshop (admin) ──────────────────────────────────────────────────────

    @app_commands.command(name="addshop", description="[Admin] Add a role to the shop.")
    @app_commands.describe(role="The role to add.", price="Price in belubucks.")
    @app_commands.default_permissions(administrator=True)
    async def addshop(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
        price: int,
    ):
        if price <= 0:
            await interaction.response.send_message("❌ Price must be positive.", ephemeral=True)
            return
        await add_shop_role(interaction.guild_id, role.id, role.name, price)
        await interaction.response.send_message(
            f"✅ Role **{role.name}** added to the shop for **{price:,} belubucks**.",
            ephemeral=True,
        )

    # ── /removeshop (admin) ───────────────────────────────────────────────────

    @app_commands.command(name="removeshop", description="[Admin] Remove a role from the shop.")
    @app_commands.describe(role="The role to remove.")
    @app_commands.default_permissions(administrator=True)
    async def removeshop(self, interaction: discord.Interaction, role: discord.Role):
        await remove_shop_role(interaction.guild_id, role.id)
        await interaction.response.send_message(
            f"✅ Role **{role.name}** removed from the shop.", ephemeral=True
        )

    # ── /give (admin) ─────────────────────────────────────────────────────────

    @app_commands.command(name="give", description="[Admin] Give belubucks to a member.")
    @app_commands.describe(member="The target member.", amount="Amount to give.")
    @app_commands.default_permissions(administrator=True)
    async def give(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        amount: int,
    ):
        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be positive.", ephemeral=True)
            return
        new_balance = await add_belubucks(member.id, interaction.guild_id, amount)
        await interaction.response.send_message(
            f"✅ **{amount:,} belubucks** given to **{member.display_name}**. New balance: **{new_balance:,}** 🪙",
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
