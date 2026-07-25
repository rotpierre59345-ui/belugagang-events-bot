"""
Events Cog — BeluGANG Mini-games automatiques.
Les events se déclenchent automatiquement toutes les 3-4 minutes
dans le channel dont le nom contient "eventsBelu€(&".
Aucune commande requise — 100% automatique.
"""

import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import random
import logging

from utils.database import add_belubucks, init_db

logger = logging.getLogger("BeluGANG.Events")

# ── Nom du channel cible ───────────────────────────────────────────────────────
EVENT_CHANNEL_NAME = "eventsBelu€(&"

# ── Récompenses ────────────────────────────────────────────────────────────────
HIGHLOW_REWARD = 100
RPS_REWARD = 75
FLAG_REWARD = 80

# ── Drapeaux pour le jeu de devinette ─────────────────────────────────────────
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
    "🇮🇹": "Italy",
    "🇪🇸": "Spain",
    "🇵🇹": "Portugal",
    "🇳🇱": "Netherlands",
    "🇧🇪": "Belgium",
    "🇸🇪": "Sweden",
    "🇳🇴": "Norway",
    "🇩🇰": "Denmark",
    "🇫🇮": "Finland",
    "🇵🇱": "Poland",
    "🇷🇺": "Russia",
    "🇨🇳": "China",
    "🇸🇦": "Saudi Arabia",
    "🇦🇷": "Argentina",
    "🇿🇦": "South Africa",
}


# ── Interactive Views ──────────────────────────────────────────────────────────


class FlashView(discord.ui.View):
    """Bouton GO! — le premier à cliquer gagne."""

    def __init__(self, reward: int):
        super().__init__(timeout=20)
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
                f"⚡ **Flash Event Terminé !**\n"
                f"🏆 **{interaction.user.display_name}** a cliqué en premier et remporte "
                f"**{self.reward} belubucks** ! (Solde : {new_balance:,} 🪙)"
            ),
            view=self,
        )
        self.stop()


class BelubuckDropView(discord.ui.View):
    """Bouton pour collecter des belubucks avant qu'ils disparaissent."""

    def __init__(self, reward: int):
        super().__init__(timeout=25)
        self.reward = reward
        self.clickers: set[int] = set()

    @discord.ui.button(label="🪙 Collect Belubucks!", style=discord.ButtonStyle.primary)
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
    """HighLow — devine si le nombre caché est plus grand, plus petit ou égal."""

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
                f"✅ Correct ! Le nombre caché était **{self.hidden}**. "
                f"Tu gagnes **{self.reward} belubucks** ! (Solde : {new_balance:,} 🪙)",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"❌ Faux. Le nombre caché était **{self.hidden}**.",
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
    """Pierre Feuille Ciseaux — joue contre le bot."""

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
    """Devinette de drapeaux — trouve le bon drapeau."""

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
                f"✅ Correct ! {self.parent.correct} "
                f"Tu gagnes **{self.parent.reward} belubucks** ! (Solde : {new_balance:,} 🪙)",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"❌ Faux. Le bon drapeau était **{self.parent.correct}**.",
                ephemeral=True,
            )


# ── Main Cog ──────────────────────────────────────────────────────────────────


class Events(commands.Cog):
    """BeluGANG mini-games automatiques — 0 commande requise."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Garde la trace du dernier event lancé par guild pour éviter les doublons
        self._last_event: dict[int, str] = {}
        self.auto_events.start()

    def cog_unload(self):
        self.auto_events.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        await init_db()
        logger.info(
            f"Events Cog prêt — events automatiques dans les channels '{EVENT_CHANNEL_NAME}' "
            f"toutes les 3-4 minutes."
        )

    # ── Tâche automatique ──────────────────────────────────────────────────────

    @tasks.loop(minutes=3)
    async def auto_events(self):
        """
        Lance un event aléatoire dans tous les channels nommés 'eventsBelu€(&'
        toutes les 3 minutes (+ délai aléatoire de 0-60s pour varier).
        """
        # Petit délai aléatoire pour que ce ne soit pas toujours pile à la même seconde
        await asyncio.sleep(random.randint(0, 60))

        for guild in self.bot.guilds:
            channel = discord.utils.find(
                lambda c: EVENT_CHANNEL_NAME in c.name,
                guild.text_channels,
            )
            if channel is None:
                continue

            # Choisit un event différent du dernier pour éviter les répétitions
            event_types = ["flash", "drop", "highlow", "rps", "flag"]
            last = self._last_event.get(guild.id)
            choices = [e for e in event_types if e != last]
            event_type = random.choice(choices)
            self._last_event[guild.id] = event_type

            try:
                await self._launch_event(channel, event_type)
                logger.info(
                    f"[{guild.name}] Event automatique lancé : {event_type} dans #{channel.name}"
                )
            except Exception as e:
                logger.error(
                    f"[{guild.name}] Erreur lors du lancement de l'event {event_type} : {e}"
                )

    @auto_events.before_loop
    async def before_auto_events(self):
        await self.bot.wait_until_ready()

    # ── Lancement d'un event ──────────────────────────────────────────────────

    async def _launch_event(self, channel: discord.TextChannel, event_type: str):
        """Poste un mini-jeu interactif dans le channel cible."""

        if event_type == "flash":
            reward = random.randint(50, 200)
            view = FlashView(reward)
            embed = discord.Embed(
                title="⚡ Flash Event !",
                description=(
                    f"Clique sur **GO!** en premier pour gagner **{reward} belubucks** !\n"
                    f"⏱️ Tu as **20 secondes** !"
                ),
                color=discord.Color.yellow(),
            )
            embed.set_footer(text="BeluGANG Events • Premier arrivé, premier servi !")
            msg = await channel.send(embed=embed, view=view)
            await asyncio.sleep(20)
            if not view.winner:
                embed.description = "⏰ Personne n'a cliqué à temps !"
                embed.color = discord.Color.red()
                await msg.edit(embed=embed, view=None)

        elif event_type == "drop":
            reward = random.randint(30, 150)
            view = BelubuckDropView(reward)
            embed = discord.Embed(
                title="🪙 Belubuck Drop !",
                description=(
                    f"Collecte les belubucks avant qu'ils disparaissent !\n"
                    f"**{reward} belubucks** pour chaque personne qui clique !\n"
                    f"⏱️ **25 secondes** !"
                ),
                color=discord.Color.gold(),
            )
            embed.set_footer(text="BeluGANG Events • Tout le monde peut gagner !")
            msg = await channel.send(embed=embed, view=view)
            await asyncio.sleep(25)
            embed.description = (
                f"⏰ Event terminé ! **{len(view.clickers)}** personne(s) ont collecté "
                f"**{reward} belubucks** chacune."
            )
            embed.color = discord.Color.greyple()
            await msg.edit(embed=embed, view=None)

        elif event_type == "highlow":
            shown = random.randint(1, 100)
            hidden = random.randint(1, 100)
            view = HighLowView(shown, hidden, HIGHLOW_REWARD)
            embed = discord.Embed(
                title="🔢 HighLow Event !",
                description=(
                    f"Le nombre affiché est **{shown}**.\n"
                    f"Le nombre caché est-il **plus grand**, **plus petit** ou **égal** ?\n"
                    f"Bonne réponse = **{HIGHLOW_REWARD} belubucks** !\n"
                    f"⏱️ **30 secondes** !"
                ),
                color=discord.Color.blue(),
            )
            embed.set_footer(text="BeluGANG Events • Fais confiance à ton instinct !")
            msg = await channel.send(embed=embed, view=view)
            await asyncio.sleep(30)
            embed.description += f"\n\n⏰ Terminé ! Le nombre caché était **{hidden}**."
            embed.color = discord.Color.greyple()
            await msg.edit(embed=embed, view=None)

        elif event_type == "rps":
            view = RPSView(RPS_REWARD)
            embed = discord.Embed(
                title="✂️ Pierre Feuille Ciseaux !",
                description=(
                    f"Joue contre le bot ! Gagne **{RPS_REWARD} belubucks** si tu bats le bot !\n"
                    f"⏱️ **30 secondes** !"
                ),
                color=discord.Color.purple(),
            )
            embed.set_footer(text="BeluGANG Events • Bats le bot !")
            msg = await channel.send(embed=embed, view=view)
            await asyncio.sleep(30)
            embed.color = discord.Color.greyple()
            await msg.edit(embed=embed, view=None)

        elif event_type == "flag":
            correct_emoji, correct_name = random.choice(list(FLAGS.items()))
            all_emojis = list(FLAGS.keys())
            wrong = random.sample([e for e in all_emojis if e != correct_emoji], 3)
            options = wrong + [correct_emoji]
            view = FlagView(correct_emoji, options, FLAG_REWARD)
            embed = discord.Embed(
                title="🌍 Devinette de Drapeaux !",
                description=(
                    f"Quel est le drapeau de **{correct_name}** ?\n"
                    f"Bonne réponse = **{FLAG_REWARD} belubucks** !\n"
                    f"⏱️ **30 secondes** !"
                ),
                color=discord.Color.green(),
            )
            embed.set_footer(text="BeluGANG Events • Connais-tu ta géographie ?")
            msg = await channel.send(embed=embed, view=view)
            await asyncio.sleep(30)
            embed.description += f"\n\n⏰ Terminé ! La réponse était **{correct_emoji} {correct_name}**."
            embed.color = discord.Color.greyple()
            await msg.edit(embed=embed, view=None)

    # ── Commandes Admin (optionnelles) ────────────────────────────────────────

    @app_commands.command(
        name="event",
        description="[Admin] Lance manuellement un event dans ce channel.",
    )
    @app_commands.describe(type="Type d'event à lancer")
    @app_commands.choices(type=[
        app_commands.Choice(name="⚡ Flash Event", value="flash"),
        app_commands.Choice(name="🪙 Belubuck Drop", value="drop"),
        app_commands.Choice(name="🔢 HighLow", value="highlow"),
        app_commands.Choice(name="✂️ Pierre Feuille Ciseaux", value="rps"),
        app_commands.Choice(name="🌍 Devinette Drapeaux", value="flag"),
        app_commands.Choice(name="🎲 Aléatoire", value="random"),
    ])
    @app_commands.default_permissions(manage_guild=True)
    async def event(self, interaction: discord.Interaction, type: str = "random"):
        event_type = random.choice(["flash", "drop", "highlow", "rps", "flag"]) if type == "random" else type
        await interaction.response.send_message(
            f"✅ Event **{event_type}** lancé dans {interaction.channel.mention} !",
            ephemeral=True,
        )
        await self._launch_event(interaction.channel, event_type)

    @app_commands.command(
        name="events_status",
        description="[Admin] Vérifie le statut des events automatiques.",
    )
    @app_commands.default_permissions(administrator=True)
    async def events_status(self, interaction: discord.Interaction):
        guild = interaction.guild
        channel = discord.utils.find(
            lambda c: EVENT_CHANNEL_NAME in c.name,
            guild.text_channels,
        )

        if channel:
            status = (
                f"✅ Channel trouvé : {channel.mention}\n"
                f"⏱️ Events automatiques toutes les **3 minutes** environ\n"
                f"🎮 Mini-jeux : Flash, Drop, HighLow, RPS, Drapeaux\n"
                f"🔄 Tâche active : **{'Oui' if self.auto_events.is_running() else 'Non'}**"
            )
        else:
            status = (
                f"❌ Aucun channel nommé `{EVENT_CHANNEL_NAME}` trouvé sur ce serveur.\n"
                f"Crée un channel avec ce nom exact pour activer les events automatiques."
            )

        embed = discord.Embed(
            title="📊 BeluGANG Events — Statut",
            description=status,
            color=discord.Color.blue() if channel else discord.Color.red(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))
