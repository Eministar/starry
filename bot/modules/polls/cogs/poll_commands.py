import discord
from discord import app_commands
from discord.ext import commands
from bot.modules.polls.services.poll_service import PollService


class PollCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = getattr(bot, "poll_service", None) or PollService(bot, bot.settings, bot.db, bot.logger)

    poll = app_commands.Group(name="poll", description="Umfrage Tools")

    @poll.command(name="create", description="Umfrage erstellen")
    @app_commands.describe(channel="Zielkanal")
    async def create(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not interaction.guild:
            return await interaction.response.send_message("Nur im Server nutzbar.", ephemeral=True)
        await interaction.response.send_modal(PollCreateModal(self.service, channel.id))


class PollCreateModal(discord.ui.Modal):
    def __init__(self, service: PollService, channel_id: int):
        super().__init__(title="📊 Umfrage erstellen")
        self.service = service
        self.channel_id = int(channel_id)
        self.question = discord.ui.TextInput(label="Frage", max_length=150, required=True)
        self.options = discord.ui.TextInput(
            label="Optionen (mit Komma trennen)",
            style=discord.TextStyle.paragraph,
            max_length=400,
            required=True,
            placeholder="Option 1, Option 2, Option 3",
        )
        self.add_item(self.question)
        self.add_item(self.options)

    async def on_submit(self, interaction: discord.Interaction):
        raw_opts = [o.strip() for o in str(self.options.value).split(",") if o.strip()]
        opts = []
        for o in raw_opts:
            if o not in opts:
                opts.append(o)
        if len(opts) < 2:
            return await interaction.response.send_message("Mindestens 2 Optionen angeben.", ephemeral=True)
        if len(opts) > 10:
            return await interaction.response.send_message("Maximal 10 Optionen.", ephemeral=True)
        channel = interaction.guild.get_channel(int(self.channel_id))
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message("Zielkanal ungültig.", ephemeral=True)
        await self.service.create_poll(interaction.guild, channel, str(self.question.value), opts, interaction.user.id)
        await interaction.response.send_message("Umfrage erstellt.", ephemeral=True)
