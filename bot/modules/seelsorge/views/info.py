from __future__ import annotations

import discord
from bot.modules.seelsorge.formatting.seelsorge_views import build_info_container


class SeelsorgeInfoView(discord.ui.LayoutView):
    def __init__(self, service, guild: discord.Guild | None = None):
        super().__init__(timeout=None)
        self.service = service
        container = build_info_container(service.settings, guild)
        self.add_item(container)
