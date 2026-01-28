import discord

from bot.modules.applications.services.application_service import ApplicationService
from bot.modules.applications.formatting.application_embeds import build_application_panel_container


class ApplicationPanelModal(discord.ui.Modal):
    def __init__(self, service: ApplicationService):
        super().__init__(title="Bewerbung")
        self.service = service
        self.questions = service._questions()
        self.inputs = []
        for q in self.questions[:5]:
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


class ApplicationPanelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Bewerbung starten",
            style=discord.ButtonStyle.primary,
            custom_id="application_panel_start",
            emoji="📝",
        )

    async def callback(self, interaction: discord.Interaction):
        if not interaction.guild or not interaction.user:
            return await interaction.response.send_message("Nur im Server nutzbar.", ephemeral=True)
        bot = interaction.client
        service = getattr(bot, "application_service", None) or ApplicationService(
            bot, bot.settings, bot.db, bot.logger
        )
        has_ticket = await service.has_open_ticket(interaction.guild.id, interaction.user.id)
        if has_ticket:
            return await interaction.response.send_message(
                "Du hast bereits ein offenes Ticket. Bitte schliesse zuerst dein Ticket.",
                ephemeral=True,
            )
        await interaction.response.send_modal(ApplicationPanelModal(service))


class ApplicationPanelView(discord.ui.LayoutView):
    def __init__(self, settings=None, guild: discord.Guild | None = None, stats: dict | None = None):
        super().__init__(timeout=None)
        total = int((stats or {}).get("total", 0) or 0)
        open_ = int((stats or {}).get("open_", 0) or 0)
        container = build_application_panel_container(settings, guild, total, open_, ApplicationPanelButton())
        self.add_item(container)
