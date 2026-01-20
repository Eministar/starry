import discord
from bot.utils.emojis import em


def parse_hex_color(value: str, default: int = 0xB16B91) -> int:
    if not value:
        return default
    v = str(value).strip().replace("#", "")
    try:
        return int(v, 16)
    except Exception:
        return default


def _color(settings, guild: discord.Guild | None):
    if guild:
        value = settings.get_guild(guild.id, "design.accent_color", "#B16B91")
    else:
        value = settings.get("design.accent_color", "#B16B91")
    return parse_hex_color(value)


def _footer(emb: discord.Embed, settings, guild: discord.Guild | None):
    if guild:
        ft = settings.get_guild(guild.id, "design.footer_text", None)
    else:
        ft = settings.get("design.footer_text", None)
    if ft:
        emb.set_footer(text=str(ft))


def build_snippet_embed(settings, guild: discord.Guild | None, key: str, title: str, body: str):
    info = em(settings, "info", guild)
    arrow2 = em(settings, "arrow2", guild)
    desc = f"{arrow2} {body}"
    emb = discord.Embed(
        title=f"{info} {title} · {key}",
        description=desc,
        color=_color(settings, guild),
    )
    _footer(emb, settings, guild)
    return emb


def build_snippet_list_embed(settings, guild: discord.Guild | None, items: list[tuple[str, str]]):
    info = em(settings, "info", guild)
    arrow2 = em(settings, "arrow2", guild)
    if not items:
        desc = f"{arrow2} Keine Snippets konfiguriert."
    else:
        lines = [f"• `{k}` - {title}" for k, title in items]
        desc = f"{arrow2} Verfügbare Snippets:\n\n" + "\n".join(lines)
    emb = discord.Embed(
        title=f"{info} Text-Snippets",
        description=desc,
        color=_color(settings, guild),
    )
    _footer(emb, settings, guild)
    return emb
