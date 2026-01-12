import discord
from bot.core.perms import is_staff


class TeamNoteModal(discord.ui.Modal):
    def __init__(self, service):
        super().__init__(title="📝 Team-Notiz")
        self.service = service
        self.note = discord.ui.TextInput(
            label="Notiz",
            required=True,
            max_length=1500,
            style=discord.TextStyle.paragraph,
            placeholder="Interne Notiz fürs Team.",
        )
        self.add_item(self.note)

    async def on_submit(self, interaction: discord.Interaction):
        text = (self.note.value or "").strip()
        await self.service.post_team_note(interaction, text)


class SummaryView(discord.ui.View):
    def __init__(self, service, ticket_id: int, claimed: bool = False):
        super().__init__(timeout=None)
        self.service = service
        self.ticket_id = int(ticket_id)
        self.claimed = bool(claimed)

        self.btn_claim = discord.ui.Button(
            custom_id="starry:ticket_claim",
            style=discord.ButtonStyle.success,
            label="Ticket beanspruchen",
            emoji="✅",
        )
        self.btn_claim.callback = self._on_claim

        self.btn_note = discord.ui.Button(
            custom_id="starry:ticket_note",
            style=discord.ButtonStyle.primary,
            label="Team-Notiz",
            emoji="📝",
        )
        self.btn_note.callback = self._on_note

        self.btn_close = discord.ui.Button(
            custom_id="starry:ticket_close",
            style=discord.ButtonStyle.danger,
            label="Ticket schließen",
            emoji="🔒",
        )
        self.btn_close.callback = self._on_close

        self.add_item(self.btn_claim)
        self.add_item(self.btn_note)
        self.add_item(self.btn_close)

        self._apply_claim_state()

    def _apply_claim_state(self):
        if self.claimed:
            self.btn_claim.label = "Ticket freigeben"
            self.btn_claim.style = discord.ButtonStyle.secondary
            self.btn_claim.emoji = "🔓"
        else:
            self.btn_claim.label = "Ticket beanspruchen"
            self.btn_claim.style = discord.ButtonStyle.success
            self.btn_claim.emoji = "✅"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            try:
                await interaction.response.send_message("Nur im Server nutzbar.", ephemeral=True)
            except discord.InteractionResponded:
                await interaction.followup.send("Nur im Server nutzbar.", ephemeral=True)
            return False

        if not is_staff(self.service.settings, interaction.user):
            try:
                await interaction.response.send_message("Keine Rechte.", ephemeral=True)
            except discord.InteractionResponded:
                await interaction.followup.send("Keine Rechte.", ephemeral=True)
            return False

        return True

    async def _on_claim(self, interaction: discord.Interaction):
        await self.service.toggle_claim(interaction)

    async def _on_note(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TeamNoteModal(self.service))

    async def _on_close(self, interaction: discord.Interaction):
        await self.service.close_ticket(interaction, "")
