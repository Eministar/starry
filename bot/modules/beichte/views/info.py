from __future__ import annotations

import discord
from bot.modules.beichte.formatting.beichte_views import build_info_container


class BeichteAnonymousYesButton(discord.ui.Button):
    def __init__(self, service):
        super().__init__(
            label="Anonym: Ja",
            style=discord.ButtonStyle.secondary,
            emoji="🕵️",
            custom_id="starry:beichte:anon_yes",
        )
        self.service = service

    async def callback(self, interaction: discord.Interaction):
        await self.service.open_submit_modal(interaction, anonymous=True)


class BeichteAnonymousNoButton(discord.ui.Button):
    def __init__(self, service):
        super().__init__(
            label="Anonym: Nein",
            style=discord.ButtonStyle.primary,
            emoji="👤",
            custom_id="starry:beichte:anon_no",
        )
        self.service = service

    async def callback(self, interaction: discord.Interaction):
        await self.service.open_submit_modal(interaction, anonymous=False)


class BeichteInfoView(discord.ui.LayoutView):
    def __init__(self, service, guild: discord.Guild | None = None):
        super().__init__(timeout=None)
        self.service = service
        container = build_info_container(
            service.settings,
            guild,
            BeichteAnonymousYesButton(service),
            BeichteAnonymousNoButton(service),
        )
        self.add_item(container)

