from __future__ import annotations

import discord
from bot.modules.wort_zum_sonntag.formatting.wort_views import build_info_container


class PingRoleButton(discord.ui.Button):
    def __init__(self, service):
        super().__init__(
            label="Ping-Rolle erhalten",
            style=discord.ButtonStyle.secondary,
            emoji="🔔",
            custom_id="starry:wzs:ping_role",
        )
        self.service = service

    async def callback(self, interaction: discord.Interaction):
        await self.service.toggle_ping_role(interaction)


class WortInfoView(discord.ui.LayoutView):
    def __init__(self, service, guild: discord.Guild | None = None):
        super().__init__(timeout=None)
        container = build_info_container(service.settings, guild, PingRoleButton(service))
        self.add_item(container)
