from __future__ import annotations

import discord
from bot.utils.emojis import em


DEFAULT_COLOR = 0xB16B91


def _color(settings, guild: discord.Guild | None) -> int:
    if guild:
        value = settings.get_guild(guild.id, "design.accent_color", "#B16B91")
    else:
        value = settings.get("design.accent_color", "#B16B91")
    v = str(value or "").replace("#", "").strip()
    try:
        return int(v, 16)
    except Exception:
        return DEFAULT_COLOR


def build_limit_view(settings, guild: discord.Guild | None, limit: int) -> discord.ui.LayoutView:
    arrow2 = em(settings, "arrow2", guild) or "»"
    info = em(settings, "info", guild) or "ℹ️"

    header = f"**{info} 𑁉 LIMIT ERREICHT**"
    body = (
        f"{arrow2} Dein Tageslimit für KI‑Antworten ist erreicht.\n\n"
        f"┏`📌` - Limit: **{int(limit)}** pro Tag\n"
        f"┗`⏳` - Info: Versuche es morgen erneut."
    )

    view = discord.ui.LayoutView(timeout=None)
    container = discord.ui.Container(accent_colour=_color(settings, guild))
    container.add_item(discord.ui.TextDisplay(f"{header}\n{body}"))
    view.add_item(container)
    return view
