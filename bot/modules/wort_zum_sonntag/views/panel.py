from __future__ import annotations

import discord
from bot.modules.wort_zum_sonntag.formatting.wort_views import build_panel_container


class WortSubmitButton(discord.ui.Button):
    def __init__(self, service):
        super().__init__(
            label="Weisheit einreichen",
            style=discord.ButtonStyle.primary,
            emoji="📜",
            custom_id="starry:wzs:submit",
        )
        self.service = service

    async def callback(self, interaction: discord.Interaction):
        await self.service.open_submit_modal(interaction)


class WortPanelView(discord.ui.LayoutView):
    def __init__(self, service, guild: discord.Guild | None = None):
        super().__init__(timeout=None)
        self.service = service
        container = build_panel_container(service.settings, guild, WortSubmitButton(service))
        self.add_item(container)
