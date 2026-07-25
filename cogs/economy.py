import discord
from discord import app_commands
from discord.ext import commands
import time
import random
from utils import get_user, update_balance, set_work_cooldown, get_leaderboard

WORK_COOLDOWN_SECONDS = 3600  # 1 hour
WORK_MIN = 50
WORK_MAX = 200

BELUBUCKS = "belubucks"

BRAND_COLOR = discord.Color.from_str("#5865F2")
SUCCESS_COLOR = discord.Color.from_str("#57F287")
ERROR_COLOR = discord.Color.from_str("#ED4245")

WORK_MESSAGES = [
    "You worked as a **fisherman** and caught a big haul!",
    "You worked as a **streamer** and got tons of donations!",
    "You worked as a **chef** and cooked an amazing meal!",
    "You worked as a **programmer** and shipped a feature!",
    "You worked as a **musician** and performed a great set!",
    "You worked as a **delivery driver** and made all your routes!",
    "You worked as a **artist** and sold some paintings!",
    "You worked as a **teacher** and inspired your students!",
]

SHOP_ITEMS = [
    {"name": "🎨 Custom Color Role", "price": 5000, "description": "Get a custom color role in the server"},
    {"name": "⭐ VIP Role", "price": 10000, "description": "Get the exclusive VIP role"},
    {"name": "🎭 Custom Nickname", "price": 2000, "description": "Set a custom nickname for 30 days"},
    {"name": "📢 Shoutout", "price": 3000, "description": "Get a shoutout in #general"},
    {"name": "🎮 Game Night Ticket", "price": 1500, "description": "Join the exclusive game night"},
]


class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="balance", description="View your balance or the balance of another user")
    @app_commands.describe(user="The user whose balance you want to view (optional)")
    async def balance(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        data = await get_user(target.id, interaction.guild_id)

        embed = discord.Embed(
            title="BeluGANG Events",
            description=f"💰 **{target.display_name}'s Balance**",
            color=BRAND_COLOR,
        )
        embed.add_field(name="Belubucks", value=f"**{data['balance']:,}** {BELUBUCKS}", inline=True)
        embed.add_field(name="Level", value=f"**{data['level']}**", inline=True)
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text="BeluGANG Events")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="work", description="Work to earn currency!")
    async def work(self, interaction: discord.Interaction):
        data = await get_user(interaction.user.id, interaction.guild_id)
        now = time.time()
        cooldown_remaining = data["work_cooldown"] - now

        if cooldown_remaining > 0:
            minutes = int(cooldown_remaining // 60)
            seconds = int(cooldown_remaining % 60)
            embed = discord.Embed(
                title="BeluGANG Events",
                description=f"⏳ You're still tired from your last job! Come back in **{minutes}m {seconds}s**.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        earned = random.randint(WORK_MIN, WORK_MAX)
        work_msg = random.choice(WORK_MESSAGES)

        await update_balance(interaction.user.id, interaction.guild_id, earned)
        await set_work_cooldown(interaction.user.id, interaction.guild_id, now + WORK_COOLDOWN_SECONDS)

        embed = discord.Embed(
            title="BeluGANG Events",
            description=f"{work_msg}\n\nYou finished working and earned **{earned:,} {BELUBUCKS}**! 💸",
            color=SUCCESS_COLOR,
        )
        embed.set_footer(text="BeluGANG Events • Come back in 1 hour to work again!")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="Send a leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer()
        rows = await get_leaderboard(interaction.guild_id, limit=10)

        embed = discord.Embed(
            title="BeluGANG Events — Leaderboard",
            description="Top 10 richest members on this server!",
            color=BRAND_COLOR,
        )

        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, row in enumerate(rows):
            member = interaction.guild.get_member(row["user_id"])
            name = member.display_name if member else f"User#{row['user_id']}"
            medal = medals[i] if i < 3 else f"**#{i + 1}**"
            lines.append(f"{medal} **{name}** — {row['balance']:,} {BELUBUCKS}")

        if not lines:
            embed.description = "No data yet! Use `/work` to start earning belubucks."
        else:
            embed.description = "\n".join(lines)

        embed.set_footer(text="BeluGANG Events")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="shop", description="Exchange currency for in-server rewards")
    async def shop(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="BeluGANG Events — Shop",
            description="Exchange your **belubucks** for exclusive rewards!\nContact a moderator after purchasing to claim your reward.",
            color=BRAND_COLOR,
        )
        for item in SHOP_ITEMS:
            embed.add_field(
                name=f"{item['name']} — {item['price']:,} {BELUBUCKS}",
                value=item["description"],
                inline=False,
            )
        embed.set_footer(text="BeluGANG Events • Earn belubucks with /work and events!")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
