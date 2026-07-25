"""
Auto-Events for BeluGANG Events bot.

Four event types cycle randomly in the configured events channel:
  1. Flash Event  — First to click GO! wins
  2. Flag Event   — Guess the correct country flag
  3. Collect Event — Collect belubucks before they disappear
  4. Rock Paper Scissors — Beat the bot's choice

The events channel is auto-detected as the first channel named "general",
"events", or "bot-events" in the guild. Override via EVENT_CHANNEL_NAME env var.
"""

import asyncio
import discord
from discord.ext import commands, tasks
import random
import time
import os
from utils import update_balance, add_xp

# ── Config ──────────────────────────────────────────────────────────────────
EVENT_CHANNEL_NAME = os.environ.get("EVENT_CHANNEL_NAME", "general")
EVENT_INTERVAL_MIN = int(os.environ.get("EVENT_INTERVAL_MIN", "15"))   # minutes
EVENT_INTERVAL_MAX = int(os.environ.get("EVENT_INTERVAL_MAX", "30"))   # minutes

FLASH_REWARD = 200
FLAG_REWARD = 150
FLAG_BONUS = 50
COLLECT_REWARD = 100
RPS_REWARD = 120

BRAND_COLOR = discord.Color.from_str("#5865F2")
SUCCESS_COLOR = discord.Color.from_str("#57F287")
ERROR_COLOR = discord.Color.from_str("#ED4245")
PINK_COLOR = discord.Color.from_str("#EB459E")

# ── Country flags data ───────────────────────────────────────────────────────
FLAGS = [
    ("Nepal", "🇳🇵"),
    ("Japan", "🇯🇵"),
    ("France", "🇫🇷"),
    ("Brazil", "🇧🇷"),
    ("Canada", "🇨🇦"),
    ("Germany", "🇩🇪"),
    ("Australia", "🇦🇺"),
    ("Mexico", "🇲🇽"),
    ("India", "🇮🇳"),
    ("Italy", "🇮🇹"),
    ("Spain", "🇪🇸"),
    ("South Korea", "🇰🇷"),
    ("United Kingdom", "🇬🇧"),
    ("United States", "🇺🇸"),
    ("Argentina", "🇦🇷"),
    ("Portugal", "🇵🇹"),
    ("Netherlands", "🇳🇱"),
    ("Sweden", "🇸🇪"),
    ("Norway", "🇳🇴"),
    ("Switzerland", "🇨🇭"),
    ("Turkey", "🇹🇷"),
    ("Saudi Arabia", "🇸🇦"),
    ("China", "🇨🇳"),
    ("Russia", "🇷🇺"),
    ("South Africa", "🇿🇦"),
    ("Egypt", "🇪🇬"),
    ("Nigeria", "🇳🇬"),
    ("Morocco", "🇲🇦"),
    ("Poland", "🇵🇱"),
    ("Ukraine", "🇺🇦"),
]

RPS_CHOICES = ["Rock 🪨", "Paper 📄", "Scissors ✂️"]
RPS_WINS = {
    "Rock 🪨": "Scissors ✂️",
    "Paper 📄": "Rock 🪨",
    "Scissors ✂️": "Paper 📄",
}


# ── Views ────────────────────────────────────────────────────────────────────

class FlashView(discord.ui.View):
    """Flash Event: first to click GO! wins."""

    def __init__(self, reward: int):
        super().__init__(timeout=60)
        self.reward = reward
        self.winner = None
        self.active = False  # becomes True after delay
        self._go_button = None
        self._build()

    def _build(self):
        btn = discord.ui.Button(
            label="Wait...",
            style=discord.ButtonStyle.secondary,
            custom_id="flash_go",
            disabled=True,
        )
        btn.callback = self.go_callback
        self._go_button = btn
        self.add_item(btn)

    async def go_callback(self, interaction: discord.Interaction):
        if not self.active:
            await interaction.response.send_message(
                "⚡ Not yet! Wait for the button to turn green!", ephemeral=True
            )
            return
        if self.winner is not None:
            await interaction.response.send_message(
                "😔 Too slow! Someone already claimed the reward.", ephemeral=True
            )
            return
        self.winner = interaction.user
        self.stop()
        for item in self.children:
            item.disabled = True

        # Give reward + XP
        await update_balance(interaction.user.id, interaction.guild.id, self.reward)
        _, new_level, leveled_up = await add_xp(interaction.user.id, interaction.guild.id, 30)

        embed = discord.Embed(
            title="BeluGANG Events — ⚡ Flash Event",
            description=(
                f"🎉 **{interaction.user.mention}** was the fastest and won **{self.reward:,} belubucks**!\n"
                f"💖 As a thank you for supporting BeluGANG, you've received an extra **{self.reward} belubucks**!"
            ),
            color=SUCCESS_COLOR,
        )
        embed.set_footer(text="BeluGANG Events")
        await interaction.response.edit_message(embed=embed, view=self)

        if leveled_up:
            await interaction.channel.send(
                embed=discord.Embed(
                    title="BeluGANG Events",
                    description=f"🎊 Congratulations {interaction.user.mention}! You are now **Level {new_level}**!",
                    color=PINK_COLOR,
                )
            )

    async def activate(self, message: discord.Message):
        """Called after a random delay to activate the GO button."""
        await asyncio.sleep(random.uniform(3, 12))
        self.active = True
        self._go_button.label = "GO! ⚡"
        self._go_button.style = discord.ButtonStyle.success
        self._go_button.disabled = False
        embed = discord.Embed(
            title="BeluGANG Events — ⚡ Flash Event",
            description="**GO! ⚡** Click the button NOW! First one wins!",
            color=SUCCESS_COLOR,
        )
        embed.set_footer(text="BeluGANG Events")
        await message.edit(embed=embed, view=self)


class FlagView(discord.ui.View):
    """Flag Event: guess the correct flag."""

    def __init__(self, correct: tuple, options: list, reward: int, bonus: int):
        super().__init__(timeout=30)
        self.correct = correct        # (country, emoji)
        self.reward = reward
        self.bonus = bonus
        self.winners: list[discord.Member] = []
        self.losers: list[discord.Member] = []
        self._build(options)

    def _build(self, options: list):
        for country, emoji in options:
            btn = discord.ui.Button(
                label=emoji,
                style=discord.ButtonStyle.primary,
                custom_id=f"flag_{country}",
            )
            btn.callback = self._make_callback(country, emoji)
            self.add_item(btn)

    def _make_callback(self, country: str, emoji: str):
        async def callback(interaction: discord.Interaction):
            if interaction.user in self.winners or interaction.user in self.losers:
                await interaction.response.send_message("You already answered!", ephemeral=True)
                return

            if country == self.correct[0]:
                self.winners.append(interaction.user)
                await update_balance(interaction.user.id, interaction.guild.id, self.reward + self.bonus)
                _, new_level, leveled_up = await add_xp(interaction.user.id, interaction.guild.id, 25)
                await interaction.response.send_message(
                    f"✅ Correct! You won **{self.reward + self.bonus:,} belubucks**! 💖",
                    ephemeral=True,
                )
                if leveled_up:
                    await interaction.channel.send(
                        embed=discord.Embed(
                            title="BeluGANG Events",
                            description=f"🎊 Congratulations {interaction.user.mention}! You are now **Level {new_level}**!",
                            color=PINK_COLOR,
                        )
                    )
            else:
                self.losers.append(interaction.user)
                await interaction.response.send_message(
                    f"❌ Wrong! The correct flag was **{self.correct[1]} {self.correct[0]}**.",
                    ephemeral=True,
                )
        return callback

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


class CollectView(discord.ui.View):
    """Collect Event: everyone who clicks in time gets a reward."""

    def __init__(self, reward: int):
        super().__init__(timeout=20)
        self.reward = reward
        self.collectors: list[discord.Member] = []

    @discord.ui.button(label="Collect Belubucks! 💰", style=discord.ButtonStyle.success, custom_id="collect_btn")
    async def collect(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.collectors:
            await interaction.response.send_message("You already collected!", ephemeral=True)
            return
        self.collectors.append(interaction.user)
        await update_balance(interaction.user.id, interaction.guild.id, self.reward)
        _, new_level, leveled_up = await add_xp(interaction.user.id, interaction.guild.id, 15)
        await interaction.response.send_message(
            f"💰 You collected **{self.reward:,} belubucks**!", ephemeral=True
        )
        if leveled_up:
            await interaction.channel.send(
                embed=discord.Embed(
                    title="BeluGANG Events",
                    description=f"🎊 Congratulations {interaction.user.mention}! You are now **Level {new_level}**!",
                    color=PINK_COLOR,
                )
            )

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


class RPSView(discord.ui.View):
    """Rock Paper Scissors: everyone plays against the bot."""

    def __init__(self, bot_choice: str, reward: int):
        super().__init__(timeout=20)
        self.bot_choice = bot_choice
        self.reward = reward
        self.results: dict[str, list[str]] = {"win": [], "lose": [], "tie": []}

    @discord.ui.button(label="Rock 🪨", style=discord.ButtonStyle.primary, custom_id="rps_rock")
    async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "Rock 🪨")

    @discord.ui.button(label="Paper 📄", style=discord.ButtonStyle.primary, custom_id="rps_paper")
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "Paper 📄")

    @discord.ui.button(label="Scissors ✂️", style=discord.ButtonStyle.primary, custom_id="rps_scissors")
    async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "Scissors ✂️")

    async def _handle(self, interaction: discord.Interaction, choice: str):
        # Check if user already played
        all_players = self.results["win"] + self.results["lose"] + self.results["tie"]
        if interaction.user.mention in all_players:
            await interaction.response.send_message("You already played!", ephemeral=True)
            return

        if choice == self.bot_choice:
            outcome = "tie"
            msg = f"🤝 It's a tie! Both chose **{choice}**."
        elif RPS_WINS[choice] == self.bot_choice:
            outcome = "win"
            msg = f"🎉 You win! **{choice}** beats **{self.bot_choice}**! You earned **{self.reward:,} belubucks**!"
            await update_balance(interaction.user.id, interaction.guild.id, self.reward)
            _, new_level, leveled_up = await add_xp(interaction.user.id, interaction.guild.id, 20)
            if leveled_up:
                await interaction.channel.send(
                    embed=discord.Embed(
                        title="BeluGANG Events",
                        description=f"🎊 Congratulations {interaction.user.mention}! You are now **Level {new_level}**!",
                        color=PINK_COLOR,
                    )
                )
        else:
            outcome = "lose"
            msg = f"😔 You lose! **{self.bot_choice}** beats **{choice}**."

        self.results[outcome].append(interaction.user.mention)
        await interaction.response.send_message(msg, ephemeral=True)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


# ── Cog ──────────────────────────────────────────────────────────────────────

class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._event_running = False
        self.auto_event_loop.start()

    def cog_unload(self):
        self.auto_event_loop.cancel()

    def _get_event_channel(self, guild: discord.Guild) -> discord.TextChannel | None:
        """Find the best channel to send events to."""
        preferred_names = [EVENT_CHANNEL_NAME, "events", "bot-events", "general", "chat"]
        for name in preferred_names:
            ch = discord.utils.get(guild.text_channels, name=name)
            if ch and ch.permissions_for(guild.me).send_messages:
                return ch
        # Fallback: first writable text channel
        for ch in guild.text_channels:
            if ch.permissions_for(guild.me).send_messages:
                return ch
        return None

    @tasks.loop(minutes=1)
    async def auto_event_loop(self):
        """Fires a random event every EVENT_INTERVAL_MIN–EVENT_INTERVAL_MAX minutes."""
        if self._event_running:
            return
        # Random chance each minute: fire if random minute matches interval
        interval = random.randint(EVENT_INTERVAL_MIN, EVENT_INTERVAL_MAX)
        if not hasattr(self, "_next_event_at"):
            self._next_event_at = time.time() + interval * 60
        if time.time() < self._next_event_at:
            return

        self._event_running = True
        try:
            for guild in self.bot.guilds:
                channel = self._get_event_channel(guild)
                if channel:
                    await self._run_random_event(channel)
        finally:
            self._event_running = False
            interval = random.randint(EVENT_INTERVAL_MIN, EVENT_INTERVAL_MAX)
            self._next_event_at = time.time() + interval * 60

    @auto_event_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()
        # Schedule first event 2-5 minutes after startup
        self._next_event_at = time.time() + random.randint(2, 5) * 60

    async def _run_random_event(self, channel: discord.TextChannel):
        event_type = random.choice(["flash", "flag", "collect", "rps"])
        if event_type == "flash":
            await self._run_flash_event(channel)
        elif event_type == "flag":
            await self._run_flag_event(channel)
        elif event_type == "collect":
            await self._run_collect_event(channel)
        else:
            await self._run_rps_event(channel)

    # ── Flash Event ──────────────────────────────────────────────────────────

    async def _run_flash_event(self, channel: discord.TextChannel):
        view = FlashView(reward=FLASH_REWARD)
        embed = discord.Embed(
            title="BeluGANG Events — ⚡ Flash Event",
            description=(
                "Wait for the **GO!** button to appear...\n"
                "Once it does, the **first to click it wins**! ⚡\n\n"
                f"Prize: **{FLASH_REWARD:,} belubucks**"
            ),
            color=BRAND_COLOR,
        )
        embed.set_footer(text="BeluGANG Events")
        message = await channel.send(embed=embed, view=view)

        # Activate button after random delay
        asyncio.create_task(view.activate(message))

        # Wait for view to finish (winner or timeout)
        await view.wait()

        if view.winner is None:
            embed = discord.Embed(
                title="BeluGANG Events — ⚡ Flash Event",
                description="⏰ Nobody clicked in time! The belubucks vanished...",
                color=ERROR_COLOR,
            )
            embed.set_footer(text="BeluGANG Events")
            for item in view.children:
                item.disabled = True
            await message.edit(embed=embed, view=view)

    # ── Flag Event ───────────────────────────────────────────────────────────

    async def _run_flag_event(self, channel: discord.TextChannel):
        correct = random.choice(FLAGS)
        # Pick 2 wrong options
        wrong_pool = [f for f in FLAGS if f[0] != correct[0]]
        wrong = random.sample(wrong_pool, 2)
        options = [correct] + wrong
        random.shuffle(options)

        view = FlagView(correct=correct, options=options, reward=FLAG_REWARD, bonus=FLAG_BONUS)
        embed = discord.Embed(
            title="BeluGANG Events — 🚩 Flag Event",
            description=(
                f"Click on the flag of **{correct[0]}** to win!\n\n"
                f"Prize: **{FLAG_REWARD + FLAG_BONUS:,} belubucks** 💖\n"
                f"*(Includes a thank-you bonus for supporting BeluGANG!)*"
            ),
            color=BRAND_COLOR,
        )
        embed.set_footer(text="BeluGANG Events • You have 30 seconds!")
        message = await channel.send(embed=embed, view=view)

        await view.wait()

        # Update message to show results
        winners_count = len(view.winners)
        losers_count = len(view.losers)
        if winners_count > 0:
            winner_mentions = ", ".join(m.mention for m in view.winners[:5])
            extra = f" and {winners_count - 5} more" if winners_count > 5 else ""
            result_text = (
                f"✅ **{winner_mentions}{extra}** guessed the flag of **{correct[1]} {correct[0]}**!\n"
                f"💖 As a thank you for supporting BeluGANG, you've received an extra **{FLAG_BONUS} belubucks**!\n\n"
                f"🏆 **{winners_count}** correct | ❌ **{losers_count}** wrong"
            )
            color = SUCCESS_COLOR
        else:
            result_text = (
                f"⏰ Nobody guessed correctly! The answer was **{correct[1]} {correct[0]}**.\n"
                f"❌ **{losers_count}** wrong answers"
            )
            color = ERROR_COLOR

        embed = discord.Embed(
            title="BeluGANG Events — 🚩 Flag Event (Ended)",
            description=result_text,
            color=color,
        )
        embed.set_footer(text="BeluGANG Events")
        for item in view.children:
            item.disabled = True
        await message.edit(embed=embed, view=view)

    # ── Collect Event ────────────────────────────────────────────────────────

    async def _run_collect_event(self, channel: discord.TextChannel):
        view = CollectView(reward=COLLECT_REWARD)
        embed = discord.Embed(
            title="BeluGANG Events — 💰 Collect Event",
            description=(
                "**Collect the belubucks before they disappear!** 💰\n\n"
                f"Click the button to grab **{COLLECT_REWARD:,} belubucks**!\n"
                "*(Everyone who clicks in time wins!)*"
            ),
            color=BRAND_COLOR,
        )
        embed.set_footer(text="BeluGANG Events • You have 20 seconds!")
        message = await channel.send(embed=embed, view=view)

        await view.wait()

        collectors_count = len(view.collectors)
        if collectors_count > 0:
            collector_mentions = ", ".join(m.mention for m in view.collectors[:5])
            extra = f" and {collectors_count - 5} more" if collectors_count > 5 else ""
            result_text = (
                f"💰 **{collector_mentions}{extra}** collected their belubucks!\n"
                f"**{collectors_count}** member(s) earned **{COLLECT_REWARD:,} belubucks** each."
            )
            color = SUCCESS_COLOR
        else:
            result_text = "⏰ Nobody collected in time! The belubucks disappeared..."
            color = ERROR_COLOR

        embed = discord.Embed(
            title="BeluGANG Events — 💰 Collect Event (Ended)",
            description=result_text,
            color=color,
        )
        embed.set_footer(text="BeluGANG Events")
        for item in view.children:
            item.disabled = True
        await message.edit(embed=embed, view=view)

    # ── Rock Paper Scissors Event ─────────────────────────────────────────────

    async def _run_rps_event(self, channel: discord.TextChannel):
        bot_choice = random.choice(RPS_CHOICES)
        view = RPSView(bot_choice=bot_choice, reward=RPS_REWARD)

        embed = discord.Embed(
            title="BeluGANG Events — 🎮 Rock Paper Scissors",
            description=(
                "**Shoot!** Play against the bot!\n\n"
                "Choose your move below. Beat the bot to win belubucks!\n"
                f"Prize: **{RPS_REWARD:,} belubucks** per winner"
            ),
            color=BRAND_COLOR,
        )
        embed.set_footer(text="BeluGANG Events • You have 20 seconds!")
        message = await channel.send(embed=embed, view=view)

        await view.wait()

        wins = len(view.results["win"])
        losses = len(view.results["lose"])
        ties = len(view.results["tie"])

        result_text = (
            f"**Shoot! The bot chose {bot_choice}!**\n\n"
            f"🏆 **{wins}** user(s) won | 😔 **{losses}** lost | 🤝 **{ties}** tied"
        )
        if wins > 0:
            winner_list = ", ".join(view.results["win"][:5])
            extra = f" and {wins - 5} more" if wins > 5 else ""
            result_text += f"\n\n🎉 Winners: {winner_list}{extra}"

        embed = discord.Embed(
            title="BeluGANG Events — 🎮 Rock Paper Scissors (Ended)",
            description=result_text,
            color=SUCCESS_COLOR if wins > 0 else ERROR_COLOR,
        )
        embed.set_footer(text="BeluGANG Events")
        for item in view.children:
            item.disabled = True
        await message.edit(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))
