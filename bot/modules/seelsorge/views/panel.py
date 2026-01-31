from __future__ import annotations

import discord
from bot.modules.seelsorge.formatting.seelsorge_views import build_panel_container


class SeelsorgeSubmitButton(discord.ui.Button):
    def __init__(self, service):
        super().__init__(
            label="Thread erstellen",
            style=discord.ButtonStyle.primary,
            emoji="🧠",
            custom_id="starry:seelsorge:submit",
        )
        self.service = service

    async def callback(self, interaction: discord.Interaction):
        await self.service.open_submit_modal(interaction)


class SeelsorgePanelView(discord.ui.LayoutView):
    def __init__(self, service, guild: discord.Guild | None = None):
        super().__init__(timeout=None)
        self.service = service
        container = build_panel_container(service.settings, guild, SeelsorgeSubmitButton(service))
        self.add_item(container)
