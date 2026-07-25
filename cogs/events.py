"""
Events Cog — BeluGANG Mini-games: Flash Event, HighLow, Rock Paper Scissors,
Flag Guessing, Belubuck Drop.
"""

import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import random
import time
import logging

from utils.database import add_belubucks, init_db

logger = logging.getLogger("BeluGANG.Events")

# Rewards per event
FLASH_REWARD = random.randint(50, 150)
HIGHLOW_REWARD = 100
RPS_REWARD = 75
FLAG_REWARD = 80
DROP_REWARD = random.randint(30, 120)

# Flags for guessing game
FLAGS = {
    "🇳🇵": "Nepal",
    "🇧🇭": "Bahrain",
    "🇨🇭": "Switzerland",
    "🇻🇦": "Vatican City",
    "🇬🇧": "United Kingdom",
    "🇯🇵": "Japan",
    "🇧🇷": "Brazil",
    "🇰🇷": "South Korea",
    "🇮🇳": "India",
    "🇫🇷": "France",
    "🇩🇪": "Germany",
    "🇺🇸": "United States",
    "🇨🇦": "Canada",
    "🇦🇺": "Australia",
    "🇲🇽": "Mexico",
}


# ── Interactive Views ──────────────────────────────────────────────────────────


class FlashView(discord.ui.View):
    """GO! button for Flash Event — first clicker wins."""

    def __init__(self, reward: int):
        super().__init__(timeout=15)
        self.reward = reward
        self.winner: discord.Member | None = None

    @discord.ui.button(label="⚡ GO!", style=discord.ButtonStyle.success)
    async def go(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.winner:
            await interaction.response.send_message(
                f"❌ Too late! **{self.winner.display_name}** already clicked.", ephemeral=True
            )
            return
        self.winner = interaction.user
        new_balance = await add_belubucks(interaction.user.id, interaction.guild_id, self.reward)
        button.disabled = True
        button.label = f"✅ Won by {interaction.user.display_name}"
        await interaction.response.edit_message(
            content=(
                f"⚡ **Flash Event Finished!**\n"
                f"🏆 **{interaction.user.display_name}** clicked first and wins "
                f"**{self.reward} belubucks**! (Balance: {new_balance:,} 🪙)"
            ),
            view=self,
        )
        self.stop()


class BelubuckDropView(discord.ui.View):
    """Button to collect belubucks before they disappear."""

    def __init__(self, reward: int):
        super().__init__(timeout=20)
        self.reward = reward
        self.clickers: set[int] = set()

    @discord.ui.button(label="🪙 Collect!", style=discord.ButtonStyle.primary)
    async def collect(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.clickers:
            await interaction.response.send_message(
                "❌ You already collected these belubucks!", ephemeral=True
            )
            return
        self.clickers.add(interaction.user.id)
        new_balance = await add_belubucks(interaction.user.id, interaction.guild_id, self.reward)
        await interaction.response.send_message(
            f"✅ You collected **{self.reward} belubucks**! Balance: **{new_balance:,}** 🪙",
            ephemeral=True,
        )


class HighLowView(discord.ui.View):
    """HighLow game — guess if the hidden number is higher, lower, or equal."""

    def __init__(self, shown: int, hidden: int, reward: int):
        super().__init__(timeout=30)
        self.shown = shown
        self.hidden = hidden
        self.reward = reward
        self.played: set[int] = set()

    async def _handle(self, interaction: discord.Interaction, guess: str):
        if interaction.user.id in self.played:
            await interaction.response.send_message("❌ You already played!", ephemeral=True)
            return
        self.played.add(interaction.user.id)

        correct = (
            (guess == "higher" and self.hidden > self.shown)
            or (guess == "lower" and self.hidden < self.shown)
            or (guess == "equal" and self.hidden == self.shown)
        )

        if correct:
            new_balance = await add_belubucks(
                interaction.user.id, interaction.guild_id, self.reward
            )
            await interaction.response.send_message(
                f"✅ Correct! The hidden number was **{self.hidden}**. "
                f"You win **{self.reward} belubucks**! (Balance: {new_balance:,} 🪙)",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"❌ Wrong. The hidden number was **{self.hidden}**.",
                ephemeral=True,
            )

    @discord.ui.button(label="⬆️ Higher", style=discord.ButtonStyle.primary)
    async def higher(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "higher")

    @discord.ui.button(label="⬇️ Lower", style=discord.ButtonStyle.danger)
    async def lower(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "lower")

    @discord.ui.button(label="🟰 Equal", style=discord.ButtonStyle.secondary)
    async def equal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "equal")


class RPSView(discord.ui.View):
    """Rock Paper Scissors — play against the bot."""

    CHOICES = {"🪨": "rock", "📄": "paper", "✂️": "scissors"}
    BEATS = {"rock": "scissors", "paper": "rock", "scissors": "paper"}

    def __init__(self, reward: int):
        super().__init__(timeout=30)
        self.reward = reward
        self.played: set[int] = set()

    async def _handle(self, interaction: discord.Interaction, player_choice: str):
        if interaction.user.id in self.played:
            await interaction.response.send_message("❌ You already played!", ephemeral=True)
            return
        self.played.add(interaction.user.id)

        bot_choice = random.choice(list(self.CHOICES.values()))
        emoji_map = {v: k for k, v in self.CHOICES.items()}

        if player_choice == bot_choice:
            result = "🤝 It's a Tie!"
            won = False
        elif self.BEATS[player_choice] == bot_choice:
            result = "🏆 You Win!"
            won = True
        else:
            result = "💀 You Lose!"
            won = False

        if won:
            new_balance = await add_belubucks(
                interaction.user.id, interaction.guild_id, self.reward
            )
            detail = f"You win **{self.reward} belubucks**! (Balance: {new_balance:,} 🪙)"
        else:
            detail = "Better luck next time!"

        await interaction.response.send_message(
            f"{emoji_map[player_choice]} vs {emoji_map[bot_choice]}\n{result}\n{detail}",
            ephemeral=True,
        )

    @discord.ui.button(label="🪨 Rock", style=discord.ButtonStyle.secondary)
    async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "rock")

    @discord.ui.button(label="📄 Paper", style=discord.ButtonStyle.secondary)
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "paper")

    @discord.ui.button(label="✂️ Scissors", style=discord.ButtonStyle.secondary)
    async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "scissors")


class FlagView(discord.ui.View):
    """Flag guessing game — find the correct flag."""

    def __init__(self, correct_emoji: str, options: list[str], reward: int):
        super().__init__(timeout=30)
        self.correct = correct_emoji
        self.reward = reward
        self.played: set[int] = set()

        random.shuffle(options)
        for emoji in options:
            self.add_item(FlagButton(emoji, emoji == correct_emoji, self))


class FlagButton(discord.ui.Button):
    def __init__(self, emoji: str, is_correct: bool, parent: FlagView):
        super().__init__(label=emoji, style=discord.ButtonStyle.secondary)
        self.is_correct = is_correct
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id in self.parent.played:
            await interaction.response.send_message("❌ You already played!", ephemeral=True)
            return
        self.parent.played.add(interaction.user.id)

        if self.is_correct:
            new_balance = await add_belubucks(
                interaction.user.id, interaction.guild_id, self.parent.reward
            )
            await interaction.response.send_message(
                f"✅ Correct! {self.parent.correct} "
                f"You win **{self.parent.reward} belubucks**! (Balance: {new_balance:,} 🪙)",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"❌ Wrong. The correct flag was **{self.parent.correct}**.",
                ephemeral=True,
            )


# ── Main Cog ──────────────────────────────────────────────────────────────


class Events(commands.Cog):
    """BeluGANG mini-games and events."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._event_channels: dict[int, int] = {}  # guild_id -> channel_id
        self.auto_events.start()

    def cog_unload(self):
        self.auto_events.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        await init_db()

    # ── Auto Task ──────────────────────────────────────────────────────

    @tasks.loop(minutes=15)
    async def auto_events(self):
        """Launches a random event in 'eventsBelu€(&' channels every 15 minutes with a Nuke."""
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                if "eventsBelu€(&" in channel.name:
                    try:
                        # Nuke logic: Delete and recreate the channel
                        position = channel.position
                        category = channel.category
                        overwrites = channel.overwrites
                        name = channel.name
                        
                        await channel.delete(reason="BeluGANG Event Nuke")
                        new_channel = await guild.create_text_channel(
                            name=name,
                            category=category,
                            overwrites=overwrites,
                            position=position,
                            reason="BeluGANG Event Reset"
                        )
                        
                        # Launch random event in the new channel
                        event_type = random.choice(["flash", "drop", "highlow", "rps", "flag"])
                        await self._launch_event(new_channel, event_type)
                        logger.info(f"Nuked and launched {event_type} in {name} on {guild.name}")
                        
                    except Exception as e:
                        logger.error(f"Failed to nuke/launch event in {channel.name} on {guild.name}: {e}")

    @auto_events.before_loop
    async def before_auto_events(self):
        await self.bot.wait_until_ready()

    # ── Event Launching ──────────────────────────────────────────────────

    async def _launch_event(self, channel: discord.TextChannel, event_type: str):
        if event_type == "flash":
            reward = random.randint(50, 150)
            view = FlashView(reward)
            embed = discord.Embed(
                title="⚡ Flash Event!",
                description=f"Click **GO!** first to win **{reward} belubucks**!",
                color=discord.Color.yellow(),
            )
            msg = await channel.send(embed=embed, view=view)
            await asyncio.sleep(15)
            if not view.winner:
                embed.description = "⏰ No one clicked in time!"
                embed.color = discord.Color.red()
                await msg.edit(embed=embed, view=None)

        elif event_type == "drop":
            reward = random.randint(30, 120)
            view = BelubuckDropView(reward)
            embed = discord.Embed(
                title="🪙 Belubuck Drop!",
                description=f"Collect the belubucks before they disappear! **{reward} belubucks** each!",
                color=discord.Color.gold(),
            )
            msg = await channel.send(embed=embed, view=view)
            await asyncio.sleep(20)
            embed.description = f"⏰ Event finished! **{len(view.clickers)}** people collected."
            embed.color = discord.Color.greyple()
            await msg.edit(embed=embed, view=None)

        elif event_type == "highlow":
            shown = random.randint(1, 100)
            hidden = random.randint(1, 100)
            reward = HIGHLOW_REWARD
            view = HighLowView(shown, hidden, reward)
            embed = discord.Embed(
                title="🔢 HighLow Event!",
                description=(
                    f"The shown number is **{shown}**.\n"
                    f"Is the hidden number **higher**, **lower**, or **equal**?\n"
                    f"Correct answer = **{reward} belubucks**!"
                ),
                color=discord.Color.blue(),
            )
            msg = await channel.send(embed=embed, view=view)
            await asyncio.sleep(30)
            embed.description += f"\n\n⏰ Finished! The hidden number was **{hidden}**."
            embed.color = discord.Color.greyple()
            await msg.edit(embed=embed, view=None)

        elif event_type == "rps":
            reward = RPS_REWARD
            view = RPSView(reward)
            embed = discord.Embed(
                title="✂️ Rock Paper Scissors!",
                description=f"Play against the bot! Win **{reward} belubucks** if you win!",
                color=discord.Color.purple(),
            )
            msg = await channel.send(embed=embed, view=view)
            await asyncio.sleep(30)
            embed.color = discord.Color.greyple()
            await msg.edit(embed=embed, view=None)

        elif event_type == "flag":
            correct_emoji, correct_name = random.choice(list(FLAGS.items()))
            all_emojis = list(FLAGS.keys())
            wrong = random.sample([e for e in all_emojis if e != correct_emoji], 3)
            options = wrong + [correct_emoji]
            reward = FLAG_REWARD
            view = FlagView(correct_emoji, options, reward)
            embed = discord.Embed(
                title="🌍 Flag Guessing Event!",
                description=(
                    f"What is the flag of **{correct_name}**?\n"
                    f"Correct answer = **{reward} belubucks**!"
                ),
                color=discord.Color.green(),
            )
            msg = await channel.send(embed=embed, view=view)
            await asyncio.sleep(30)
            embed.color = discord.Color.greyple()
            await msg.edit(embed=embed, view=None)

    # ── Slash Commands ────────────────────────────────────────────────────────

    @app_commands.command(name="flash", description="Launch a Flash Event in this channel.")
    @app_commands.default_permissions(manage_guild=True)
    async def flash(self, interaction: discord.Interaction):
        await interaction.response.send_message("⚡ Flash Event launched!", ephemeral=True)
        await self._launch_event(interaction.channel, "flash")

    @app_commands.command(name="drop", description="Launch a Belubuck Drop in this channel.")
    @app_commands.default_permissions(manage_guild=True)
    async def drop(self, interaction: discord.Interaction):
        await interaction.response.send_message("🪙 Belubuck Drop launched!", ephemeral=True)
        await self._launch_event(interaction.channel, "drop")

    @app_commands.command(name="highlow", description="Launch a HighLow Event in this channel.")
    @app_commands.default_permissions(manage_guild=True)
    async def highlow(self, interaction: discord.Interaction):
        await interaction.response.send_message("🔢 HighLow Event launched!", ephemeral=True)
        await self._launch_event(interaction.channel, "highlow")

    @app_commands.command(name="rps", description="Launch a Rock Paper Scissors Event.")
    @app_commands.default_permissions(manage_guild=True)
    async def rps(self, interaction: discord.Interaction):
        await interaction.response.send_message("✂️ RPS Event launched!", ephemeral=True)
        await self._launch_event(interaction.channel, "rps")

    @app_commands.command(name="flag", description="Launch a Flag Guessing Event.")
    @app_commands.default_permissions(manage_guild=True)
    async def flag(self, interaction: discord.Interaction):
        await interaction.response.send_message("🌍 Flag Event launched!", ephemeral=True)
        await self._launch_event(interaction.channel, "flag")

    @app_commands.command(
        name="seteventchannel",
        description="[Admin] Set the channel for auto events.",
    )
    @app_commands.default_permissions(administrator=True)
    async def seteventchannel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ):
        self._event_channels[interaction.guild_id] = channel.id
        await interaction.response.send_message(
            f"✅ Event channel set to {channel.mention}. "
            f"Auto events will happen every 15 minutes.",
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))
