"""
Cog Événements — Mini-jeux BeluGANG : Flash Event, HighLow, Rock Paper Scissors,
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

# Récompenses par événement
FLASH_REWARD = random.randint(50, 150)
HIGHLOW_REWARD = 100
RPS_REWARD = 75
FLAG_REWARD = 80
DROP_REWARD = random.randint(30, 120)

# Drapeaux pour le jeu de devinette
FLAGS = {
    "🇳🇵": "Népal",
    "🇧🇭": "Bahreïn",
    "🇨🇭": "Suisse",
    "🇻🇦": "Vatican",
    "🇬🇧": "Royaume-Uni",
    "🇯🇵": "Japon",
    "🇧🇷": "Brésil",
    "🇰🇷": "Corée du Sud",
    "🇮🇳": "Inde",
    "🇫🇷": "France",
    "🇩🇪": "Allemagne",
    "🇺🇸": "États-Unis",
    "🇨🇦": "Canada",
    "🇦🇺": "Australie",
    "🇲🇽": "Mexique",
}


# ── Vues interactives ──────────────────────────────────────────────────────────


class FlashView(discord.ui.View):
    """Bouton GO! pour le Flash Event — premier cliqueur gagne."""

    def __init__(self, reward: int):
        super().__init__(timeout=15)
        self.reward = reward
        self.winner: discord.Member | None = None

    @discord.ui.button(label="⚡ GO!", style=discord.ButtonStyle.success)
    async def go(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.winner:
            await interaction.response.send_message(
                f"❌ Trop tard ! **{self.winner.display_name}** a déjà cliqué.", ephemeral=True
            )
            return
        self.winner = interaction.user
        new_balance = await add_belubucks(interaction.user.id, interaction.guild_id, self.reward)
        button.disabled = True
        button.label = f"✅ Gagné par {interaction.user.display_name}"
        await interaction.response.edit_message(
            content=(
                f"⚡ **Flash Event terminé !**\n"
                f"🏆 **{interaction.user.display_name}** a cliqué en premier et remporte "
                f"**{self.reward} belubucks** ! (Solde : {new_balance:,} 🪙)"
            ),
            view=self,
        )
        self.stop()


class BelubuckDropView(discord.ui.View):
    """Bouton pour collecter des belubucks avant qu'ils disparaissent."""

    def __init__(self, reward: int):
        super().__init__(timeout=20)
        self.reward = reward
        self.clickers: set[int] = set()

    @discord.ui.button(label="🪙 Collecter !", style=discord.ButtonStyle.primary)
    async def collect(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.clickers:
            await interaction.response.send_message(
                "❌ Tu as déjà collecté ces belubucks !", ephemeral=True
            )
            return
        self.clickers.add(interaction.user.id)
        new_balance = await add_belubucks(interaction.user.id, interaction.guild_id, self.reward)
        await interaction.response.send_message(
            f"✅ Tu as collecté **{self.reward} belubucks** ! Solde : **{new_balance:,}** 🪙",
            ephemeral=True,
        )


class HighLowView(discord.ui.View):
    """Jeu HighLow — deviner si le nombre caché est plus haut, plus bas ou égal."""

    def __init__(self, shown: int, hidden: int, reward: int):
        super().__init__(timeout=30)
        self.shown = shown
        self.hidden = hidden
        self.reward = reward
        self.played: set[int] = set()

    async def _handle(self, interaction: discord.Interaction, guess: str):
        if interaction.user.id in self.played:
            await interaction.response.send_message("❌ Tu as déjà joué !", ephemeral=True)
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
                f"✅ Bonne réponse ! Le nombre caché était **{self.hidden}**. "
                f"Tu gagnes **{self.reward} belubucks** ! (Solde : {new_balance:,} 🪙)",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"❌ Mauvaise réponse. Le nombre caché était **{self.hidden}**.",
                ephemeral=True,
            )

    @discord.ui.button(label="⬆️ Plus haut", style=discord.ButtonStyle.primary)
    async def higher(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "higher")

    @discord.ui.button(label="⬇️ Plus bas", style=discord.ButtonStyle.danger)
    async def lower(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "lower")

    @discord.ui.button(label="🟰 Égal", style=discord.ButtonStyle.secondary)
    async def equal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "equal")


class RPSView(discord.ui.View):
    """Rock Paper Scissors — jouer contre le bot."""

    CHOICES = {"🪨": "rock", "📄": "paper", "✂️": "scissors"}
    BEATS = {"rock": "scissors", "paper": "rock", "scissors": "paper"}

    def __init__(self, reward: int):
        super().__init__(timeout=30)
        self.reward = reward
        self.played: set[int] = set()

    async def _handle(self, interaction: discord.Interaction, player_choice: str):
        if interaction.user.id in self.played:
            await interaction.response.send_message("❌ Tu as déjà joué !", ephemeral=True)
            return
        self.played.add(interaction.user.id)

        bot_choice = random.choice(list(self.CHOICES.values()))
        emoji_map = {v: k for k, v in self.CHOICES.items()}

        if player_choice == bot_choice:
            result = "🤝 Égalité !"
            won = False
        elif self.BEATS[player_choice] == bot_choice:
            result = "🏆 Tu gagnes !"
            won = True
        else:
            result = "💀 Tu perds !"
            won = False

        if won:
            new_balance = await add_belubucks(
                interaction.user.id, interaction.guild_id, self.reward
            )
            detail = f"Tu gagnes **{self.reward} belubucks** ! (Solde : {new_balance:,} 🪙)"
        else:
            detail = "Meilleure chance la prochaine fois !"

        await interaction.response.send_message(
            f"{emoji_map[player_choice]} vs {emoji_map[bot_choice]}\n{result}\n{detail}",
            ephemeral=True,
        )

    @discord.ui.button(label="🪨 Pierre", style=discord.ButtonStyle.secondary)
    async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "rock")

    @discord.ui.button(label="📄 Papier", style=discord.ButtonStyle.secondary)
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "paper")

    @discord.ui.button(label="✂️ Ciseaux", style=discord.ButtonStyle.secondary)
    async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "scissors")


class FlagView(discord.ui.View):
    """Jeu de devinette de drapeaux — trouver le bon drapeau."""

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
            await interaction.response.send_message("❌ Tu as déjà joué !", ephemeral=True)
            return
        self.parent.played.add(interaction.user.id)

        if self.is_correct:
            new_balance = await add_belubucks(
                interaction.user.id, interaction.guild_id, self.parent.reward
            )
            await interaction.response.send_message(
                f"✅ Bonne réponse ! {self.parent.correct} "
                f"Tu gagnes **{self.parent.reward} belubucks** ! (Solde : {new_balance:,} 🪙)",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"❌ Mauvaise réponse. Le bon drapeau était **{self.parent.correct}**.",
                ephemeral=True,
            )


# ── Cog principal ──────────────────────────────────────────────────────────────


class Events(commands.Cog):
    """Mini-jeux et événements BeluGANG."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._event_channels: dict[int, int] = {}  # guild_id -> channel_id
        self.auto_events.start()

    def cog_unload(self):
        self.auto_events.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        await init_db()

    # ── Tâche automatique ──────────────────────────────────────────────────────

    @tasks.loop(minutes=15)
    async def auto_events(self):
        """Lance un événement aléatoire dans les canaux configurés toutes les 15 minutes."""
        for guild in self.bot.guilds:
            channel_id = self._event_channels.get(guild.id)
            if not channel_id:
                continue
            channel = guild.get_channel(channel_id)
            if not channel:
                continue
            event_type = random.choice(["flash", "drop", "highlow", "rps", "flag"])
            try:
                await self._launch_event(channel, event_type)
            except Exception as e:
                logger.error(f"Erreur événement auto ({event_type}) sur {guild.name}: {e}")

    @auto_events.before_loop
    async def before_auto_events(self):
        await self.bot.wait_until_ready()

    # ── Lancement d'événement ──────────────────────────────────────────────────

    async def _launch_event(self, channel: discord.TextChannel, event_type: str):
        if event_type == "flash":
            reward = random.randint(50, 150)
            view = FlashView(reward)
            embed = discord.Embed(
                title="⚡ Flash Event !",
                description=f"Clique sur **GO!** en premier pour gagner **{reward} belubucks** !",
                color=discord.Color.yellow(),
            )
            msg = await channel.send(embed=embed, view=view)
            await asyncio.sleep(15)
            if not view.winner:
                embed.description = "⏰ Personne n'a cliqué à temps !"
                embed.color = discord.Color.red()
                await msg.edit(embed=embed, view=None)

        elif event_type == "drop":
            reward = random.randint(30, 120)
            view = BelubuckDropView(reward)
            embed = discord.Embed(
                title="🪙 Belubuck Drop !",
                description=f"Collecte les belubucks avant qu'ils disparaissent ! **{reward} belubucks** chacun !",
                color=discord.Color.gold(),
            )
            msg = await channel.send(embed=embed, view=view)
            await asyncio.sleep(20)
            embed.description = f"⏰ L'événement est terminé ! **{len(view.clickers)}** personnes ont collecté."
            embed.color = discord.Color.greyple()
            await msg.edit(embed=embed, view=None)

        elif event_type == "highlow":
            shown = random.randint(1, 100)
            hidden = random.randint(1, 100)
            reward = HIGHLOW_REWARD
            view = HighLowView(shown, hidden, reward)
            embed = discord.Embed(
                title="🔢 HighLow Event !",
                description=(
                    f"Le nombre affiché est **{shown}**.\n"
                    f"Le nombre caché est-il **plus haut**, **plus bas** ou **égal** ?\n"
                    f"Bonne réponse = **{reward} belubucks** !"
                ),
                color=discord.Color.blue(),
            )
            msg = await channel.send(embed=embed, view=view)
            await asyncio.sleep(30)
            embed.description += f"\n\n⏰ Terminé ! Le nombre caché était **{hidden}**."
            embed.color = discord.Color.greyple()
            await msg.edit(embed=embed, view=None)

        elif event_type == "rps":
            reward = RPS_REWARD
            view = RPSView(reward)
            embed = discord.Embed(
                title="✂️ Rock Paper Scissors !",
                description=f"Joue contre le bot ! Gagne **{reward} belubucks** si tu l'emportes !",
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
                title="🌍 Flag Guessing Event !",
                description=(
                    f"Quel est le drapeau du **{correct_name}** ?\n"
                    f"Bonne réponse = **{reward} belubucks** !"
                ),
                color=discord.Color.green(),
            )
            msg = await channel.send(embed=embed, view=view)
            await asyncio.sleep(30)
            embed.color = discord.Color.greyple()
            await msg.edit(embed=embed, view=None)

    # ── Commandes slash ────────────────────────────────────────────────────────

    @app_commands.command(name="flash", description="Lancer un Flash Event dans ce canal.")
    @app_commands.default_permissions(manage_guild=True)
    async def flash(self, interaction: discord.Interaction):
        await interaction.response.send_message("⚡ Flash Event lancé !", ephemeral=True)
        await self._launch_event(interaction.channel, "flash")

    @app_commands.command(name="drop", description="Lancer un Belubuck Drop dans ce canal.")
    @app_commands.default_permissions(manage_guild=True)
    async def drop(self, interaction: discord.Interaction):
        await interaction.response.send_message("🪙 Belubuck Drop lancé !", ephemeral=True)
        await self._launch_event(interaction.channel, "drop")

    @app_commands.command(name="highlow", description="Lancer un HighLow Event dans ce canal.")
    @app_commands.default_permissions(manage_guild=True)
    async def highlow(self, interaction: discord.Interaction):
        await interaction.response.send_message("🔢 HighLow Event lancé !", ephemeral=True)
        await self._launch_event(interaction.channel, "highlow")

    @app_commands.command(name="rps", description="Lancer un Rock Paper Scissors Event.")
    @app_commands.default_permissions(manage_guild=True)
    async def rps(self, interaction: discord.Interaction):
        await interaction.response.send_message("✂️ RPS Event lancé !", ephemeral=True)
        await self._launch_event(interaction.channel, "rps")

    @app_commands.command(name="flag", description="Lancer un Flag Guessing Event.")
    @app_commands.default_permissions(manage_guild=True)
    async def flag(self, interaction: discord.Interaction):
        await interaction.response.send_message("🌍 Flag Event lancé !", ephemeral=True)
        await self._launch_event(interaction.channel, "flag")

    @app_commands.command(
        name="seteventchannel",
        description="[Admin] Définir le canal pour les événements automatiques.",
    )
    @app_commands.default_permissions(administrator=True)
    async def seteventchannel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ):
        self._event_channels[interaction.guild_id] = channel.id
        await interaction.response.send_message(
            f"✅ Canal d'événements défini sur {channel.mention}. "
            f"Les événements automatiques s'y dérouleront toutes les 15 minutes.",
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))
