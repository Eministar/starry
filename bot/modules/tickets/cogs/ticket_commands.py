import discord
from discord import app_commands
from discord.ext import commands

from bot.modules.tickets.services.ticket_service import TicketService
from bot.core.perms import is_staff


class TicketCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = getattr(bot, "ticket_service", None) or TicketService(bot, bot.settings, bot.db, bot.logger)

    ticket = app_commands.Group(name="ticket", description="Ticket Tools")

    @ticket.command(name="beanspruchen", description="Ticket claimen/freigeben im aktuellen Thread")
    async def claim(self, interaction: discord.Interaction):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Nur im Server nutzbar.", ephemeral=True)
        if not is_staff(self.bot.settings, interaction.user):
            return await interaction.response.send_message("Keine Rechte.", ephemeral=True)
        await self.service.toggle_claim(interaction)

    @ticket.command(name="schliessen", description="Ticket schließen im aktuellen Thread")
    async def close(self, interaction: discord.Interaction):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Nur im Server nutzbar.", ephemeral=True)
        if not is_staff(self.bot.settings, interaction.user):
            return await interaction.response.send_message("Keine Rechte.", ephemeral=True)
        await interaction.response.send_message('Nutze bitte den Button "Ticket schließen" im Embed.', ephemeral=True)

    @app_commands.command(name="ticket-add", description="User zum aktuellen Ticket hinzufügen")
    @app_commands.describe(user="User, der zum Ticket hinzugefügt werden soll")
    async def ticket_add(self, interaction: discord.Interaction, user: discord.User):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Nur im Server nutzbar.", ephemeral=True)
        if not is_staff(self.bot.settings, interaction.user):
            return await interaction.response.send_message("Keine Rechte.", ephemeral=True)
        await self.service.add_participant(interaction, user)

    @ticket.command(name="reopen", description="Geschlossenes Ticket wieder öffnen")
    async def reopen(self, interaction: discord.Interaction):
        await self.service.reopen_ticket(interaction)

    @ticket.command(name="status", description="Ticket-Status (Label) ändern")
    @app_commands.describe(label="z.B. wartet_auf_user, on_hold, in_arbeit")
    async def status(self, interaction: discord.Interaction, label: str):
        await self.service.set_status_label(interaction, label)

    @ticket.command(name="priority", description="Ticket-Priorität setzen")
    @app_commands.choices(priority=[
        app_commands.Choice(name="Niedrig (1)", value=1),
        app_commands.Choice(name="Normal (2)", value=2),
        app_commands.Choice(name="Hoch (3)", value=3),
        app_commands.Choice(name="Dringend (4)", value=4),
    ])
    async def priority(self, interaction: discord.Interaction, priority: app_commands.Choice[int]):
        await self.service.set_priority(interaction, int(priority.value))

    @ticket.command(name="escalate", description="Ticket eskalieren")
    @app_commands.describe(level="1-5", reason="Optionaler Grund")
    async def escalate(self, interaction: discord.Interaction, level: int, reason: str | None = None):
        await self.service.escalate_ticket(interaction, level, reason)

    @ticket.command(name="category", description="Ticket-Kategorie/Tag wechseln")
    @app_commands.describe(key="Kategorie-Key aus config.yml")
    async def category(self, interaction: discord.Interaction, key: str):
        await self.service.change_category(interaction, key)

    @ticket.command(name="transcript", description="Transcript des Tickets erstellen")
    @app_commands.describe(channel="Optionaler Zielkanal (sonst Ticket-Log)")
    async def transcript(self, interaction: discord.Interaction, channel: discord.TextChannel | None = None):
        await self.service.send_transcript(interaction, channel)

    @ticket.command(name="weiterleitung", description="Ticket an eine Rolle weiterleiten")
    @app_commands.describe(role="Zielrolle", reason="Optionaler Grund")
    async def forward(self, interaction: discord.Interaction, role: discord.Role, reason: str | None = None):
        await self.service.forward_ticket(interaction, role, reason)
