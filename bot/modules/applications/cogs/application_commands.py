import discord
from discord import app_commands
from discord.ext import commands

from bot.modules.applications.services.application_service import ApplicationService


class _ApplicationModal(discord.ui.Modal):
    def __init__(self, service: ApplicationService, questions: list[str]):
        super().__init__(title="Bewerbung")
        self.service = service
        self.questions = questions
        self.inputs = []
        for q in questions[:5]:
            inp = discord.ui.TextInput(
                label=str(q)[:45],
                style=discord.TextStyle.paragraph,
                max_length=800,
                required=True,
            )
            self.inputs.append(inp)
            self.add_item(inp)

    async def on_submit(self, interaction: discord.Interaction):
        answers = [(i.value or "").strip() for i in self.inputs]
        ok, err = await self.service.start_application(interaction, answers)
        if ok:
            await interaction.response.send_message("Bewerbung wurde eingereicht. Danke!", ephemeral=True)
        else:
            await interaction.response.send_message(f"Bewerbung konnte nicht gestartet werden: {err}", ephemeral=True)


class ApplicationCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = ApplicationService(bot, bot.settings, bot.db, bot.logger)

    @app_commands.command(name="bewerbung", description="Bewerbung starten")
    async def application_start(self, interaction: discord.Interaction):
        if not interaction.guild or not interaction.user:
            return await interaction.response.send_message("Nur im Server nutzbar.", ephemeral=True)
        has_ticket = await self.service.has_open_ticket(interaction.guild.id, interaction.user.id)
        if has_ticket:
            return await interaction.response.send_message(
                "Du hast bereits ein offenes Ticket. Bitte schließe zuerst dein Ticket, bevor du dich bewirbst.",
                ephemeral=True,
            )
        await self.service.start_dm_flow(interaction.user, interaction.guild)
        await interaction.response.send_message("Ich habe dir eine DM geschickt. Bitte beantworte dort die Fragen.", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.guild is not None:
            return
        await self.service.handle_dm_answer(message)
