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


def build_application_embed(settings, guild: discord.Guild | None, user: discord.User, questions: list[str], answers: list[str]):
    info = em(settings, "info", guild) or "ℹ️"
    desc = "Neue Bewerbung eingegangen."
    emb = discord.Embed(title=f"{info} Bewerbung", description=desc, color=_color(settings, guild))
    emb.set_author(name=user.display_name, icon_url=user.display_avatar.url)
    for idx, q in enumerate(questions):
        a = answers[idx] if idx < len(answers) else "-"
        emb.add_field(name=f"{idx + 1}. {q}", value=a[:1024] or "-", inline=False)
    _footer(emb, settings, guild)
    return emb


def build_application_dm_embed(settings, guild: discord.Guild | None, questions: list[str]):
    info = em(settings, "info", guild) or "ℹ️"
    lines = [f"{i+1}. {q}" for i, q in enumerate(questions)]
    desc = "Bitte beantworte die folgenden Fragen:\n\n" + "\n".join(lines)
    emb = discord.Embed(title=f"{info} Bewerbung starten", description=desc, color=_color(settings, guild))
    _footer(emb, settings, guild)
    return emb


def build_application_panel_embed(
    settings,
    guild: discord.Guild | None,
    total: int,
    open_: int,
):
    pen = em(settings, "pen", guild) or "📝"
    arrow2 = em(settings, "arrow2", guild) or "»"
    info = em(settings, "info", guild) or "ℹ️"
    emb = discord.Embed(
        title=f"{pen} 𑁉 BEWERBUNGS-PANEL",
        description=(
            f"{arrow2} Du moechtest Teil des Teams werden? Starte deine Bewerbung direkt hier.\n\n"
            "Klick auf den Button und beantworte die Fragen ehrlich und klar."
        ),
        color=_color(settings, guild),
    )
    emb.add_field(
        name="Ablauf",
        value=(
            "1) Button klicken\n"
            "2) Fragen beantworten\n"
            "3) Wir pruefen deine Bewerbung\n"
            "4) Rueckmeldung im Thread"
        ),
        inline=False,
    )
    emb.add_field(
        name=f"{info} Live-Stats",
        value=(
            f"Bewerbungen gesamt: **{total}**\n"
            f"Offen: **{open_}**"
        ),
        inline=False,
    )
    if guild and guild.icon:
        emb.set_thumbnail(url=guild.icon.url)
    _footer(emb, settings, guild)
    return emb
