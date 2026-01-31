import random
import discord
from discord import app_commands
from discord.ext import commands


class FunCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="hug", description="🤗 𑁉 Umarmung geben")
    @app_commands.describe(user="Wen du umarmen willst")
    async def hug(self, interaction: discord.Interaction, user: discord.Member | None = None):
        msg = _build_action_message(interaction.user, user, "umarmt", _HUG_SELF, _HUG_OTHER, _HUG_SOLO)
        await interaction.response.send_message(msg)

    @app_commands.command(name="kiss", description="💋 𑁉 Kuss verteilen")
    @app_commands.describe(user="Wen du küssen willst")
    async def kiss(self, interaction: discord.Interaction, user: discord.Member | None = None):
        msg = _build_action_message(interaction.user, user, "küsst", _KISS_SELF, _KISS_OTHER, _KISS_SOLO)
        await interaction.response.send_message(msg)

    @app_commands.command(name="slap", description="🖐️ 𑁉 Klatsche verteilen")
    @app_commands.describe(user="Wen du klatschen willst")
    async def slap(self, interaction: discord.Interaction, user: discord.Member | None = None):
        msg = _build_action_message(interaction.user, user, "klatscht", _SLAP_SELF, _SLAP_OTHER, _SLAP_SOLO)
        await interaction.response.send_message(msg)

    @app_commands.command(name="pat", description="🫳 𑁉 Kopf streicheln")
    @app_commands.describe(user="Wen du streicheln willst")
    async def pat(self, interaction: discord.Interaction, user: discord.Member | None = None):
        msg = _build_action_message(interaction.user, user, "streichelt", _PAT_SELF, _PAT_OTHER, _PAT_SOLO)
        await interaction.response.send_message(msg)

    @app_commands.command(name="highfive", description="🙏 𑁉 High-Five geben")
    @app_commands.describe(user="Wem du einen High-Five gibst")
    async def highfive(self, interaction: discord.Interaction, user: discord.Member | None = None):
        msg = _build_action_message(interaction.user, user, "gibt einen High-Five", _HIGHFIVE_SELF, _HIGHFIVE_OTHER, _HIGHFIVE_SOLO)
        await interaction.response.send_message(msg)

    @app_commands.command(name="boop", description="👃 𑁉 Boop auf die Nase")
    @app_commands.describe(user="Wen du boopen willst")
    async def boop(self, interaction: discord.Interaction, user: discord.Member | None = None):
        msg = _build_action_message(interaction.user, user, "boopt", _BOOP_SELF, _BOOP_OTHER, _BOOP_SOLO)
        await interaction.response.send_message(msg)

    @app_commands.command(name="coinflip", description="🪙 𑁉 Münzwurf")
    async def coinflip(self, interaction: discord.Interaction):
        result = random.choice(["Kopf", "Zahl"])
        await interaction.response.send_message(f"🪙 Die Münze zeigt **{result}**.")

    @app_commands.command(name="dice", description="🎲 𑁉 Würfeln")
    @app_commands.describe(sides="Wie viele Seiten (2-100)")
    async def dice(self, interaction: discord.Interaction, sides: int | None = None):
        sides = int(sides or 6)
        if sides < 2 or sides > 100:
            return await interaction.response.send_message("Bitte 2 bis 100 Seiten angeben.", ephemeral=True)
        roll = random.randint(1, sides)
        await interaction.response.send_message(f"🎲 {interaction.user.mention} würfelt **{roll}** (1-{sides}).")

    @app_commands.command(name="rps", description="✂️ 𑁉 Schere, Stein, Papier")
    @app_commands.describe(choice="Deine Wahl")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Stein", value="stein"),
        app_commands.Choice(name="Papier", value="papier"),
        app_commands.Choice(name="Schere", value="schere"),
    ])
    async def rps(self, interaction: discord.Interaction, choice: app_commands.Choice[str]):
        bot_choice = random.choice(["stein", "papier", "schere"])
        outcome = _rps_outcome(choice.value, bot_choice)
        await interaction.response.send_message(
            f"✂️ {interaction.user.mention} wählt **{choice.name}**, Bot wählt **{_rps_label(bot_choice)}** → **{outcome}**."
        )

    @app_commands.command(name="8ball", description="🎱 𑁉 Magische 8-Ball Antwort")
    @app_commands.describe(question="Deine Frage")
    async def eight_ball(self, interaction: discord.Interaction, question: str):
        answer = random.choice(_EIGHTBALL_ANSWERS)
        await interaction.response.send_message(f"🎱 **Frage:** {question}\n**Antwort:** {answer}")


def _build_action_message(
    actor: discord.Member | discord.User,
    target: discord.Member | discord.User | None,
    verb: str,
    self_msgs: list[str],
    other_msgs: list[str],
    solo_msgs: list[str],
) -> str:
    if target is None:
        return random.choice(solo_msgs).format(actor=actor.mention)
    if target.id == actor.id:
        return random.choice(self_msgs).format(actor=actor.mention)
    return random.choice(other_msgs).format(actor=actor.mention, target=target.mention)


def _rps_outcome(user_choice: str, bot_choice: str) -> str:
    if user_choice == bot_choice:
        return "Unentschieden"
    beats = {"stein": "schere", "schere": "papier", "papier": "stein"}
    return "Du gewinnst" if beats[user_choice] == bot_choice else "Bot gewinnt"


def _rps_label(choice: str) -> str:
    return {"stein": "Stein", "papier": "Papier", "schere": "Schere"}[choice]


_HUG_SOLO = [
    "{actor} umarmt die Luft. 🤗",
    "{actor} schickt eine Umarmung in die Welt. ✨",
]
_HUG_SELF = [
    "{actor} umarmt sich selbst. Selfcare! 🤗",
]
_HUG_OTHER = [
    "{actor} umarmt {target}. 🤗",
    "{actor} gibt {target} eine warme Umarmung. 🫂",
]

_KISS_SOLO = [
    "{actor} verteilt Küsschen in die Runde. 💋",
    "{actor} schickt einen Kuss in die Luft. 💋",
]
_KISS_SELF = [
    "{actor} küsst sich selbst. 😘",
]
_KISS_OTHER = [
    "{actor} küsst {target}. 💋",
    "{actor} gibt {target} einen süßen Kuss. 😘",
]

_SLAP_SOLO = [
    "{actor} schlägt ins Leere. 🖐️",
    "{actor} lässt die Hand klatschen. 👏",
]
_SLAP_SELF = [
    "{actor} klatscht sich selbst. Aua. 🖐️",
]
_SLAP_OTHER = [
    "{actor} klatscht {target}. 🖐️",
    "{actor} verpasst {target} eine Klatsche. 💥",
]

_PAT_SOLO = [
    "{actor} verteilt virtuelle Pats. 🫳",
]
_PAT_SELF = [
    "{actor} streichelt sich selbst. 🫶",
]
_PAT_OTHER = [
    "{actor} streichelt {target} den Kopf. 🫳",
    "{actor} gibt {target} ein sanftes Kopftätscheln. 😊",
]

_HIGHFIVE_SOLO = [
    "{actor} gibt sich selbst einen High-Five. 🙌",
]
_HIGHFIVE_SELF = [
    "{actor} klatscht in die eigenen Hände. 🙌",
]
_HIGHFIVE_OTHER = [
    "{actor} gibt {target} einen High-Five. 🙌",
    "{actor} und {target} machen einen High-Five. ✋",
]

_BOOP_SOLO = [
    "{actor} boopt die Luft. 👃",
]
_BOOP_SELF = [
    "{actor} boopt sich selbst auf die Nase. 👃",
]
_BOOP_OTHER = [
    "{actor} boopt {target} auf die Nase. 👃",
    "{actor} stupst {target} an der Nase. ✨",
]

_EIGHTBALL_ANSWERS = [
    "Ja.",
    "Nein.",
    "Vielleicht.",
    "Frag später nochmal.",
    "Sieht gut aus.",
    "Eher nicht.",
    "Definitiv!",
    "Unklar.",
    "Auf jeden Fall.",
    "Lieber nicht.",
]
