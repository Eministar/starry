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


def _color(settings):
    return parse_hex_color(settings.get("design.accent_color", "#B16B91"))


def _footer(emb: discord.Embed, settings):
    ft = settings.get("design.footer_text", None)
    if ft:
        emb.set_footer(text=str(ft))


def build_application_embed(settings, guild: discord.Guild | None, user: discord.User, questions: list[str], answers: list[str]):
    info = em(settings, "info", guild) or "ℹ️"
    desc = "Neue Bewerbung eingegangen."
    emb = discord.Embed(title=f"{info} Bewerbung", description=desc, color=_color(settings))
    emb.set_author(name=user.display_name, icon_url=user.display_avatar.url)
    for idx, q in enumerate(questions):
        a = answers[idx] if idx < len(answers) else "-"
        emb.add_field(name=f"{idx + 1}. {q}", value=a[:1024] or "-", inline=False)
    _footer(emb, settings)
    return emb


def build_application_dm_embed(settings, guild: discord.Guild | None, questions: list[str]):
    info = em(settings, "info", guild) or "ℹ️"
    lines = [f"{i+1}. {q}" for i, q in enumerate(questions)]
    desc = "Bitte beantworte die folgenden Fragen:\n\n" + "\n".join(lines)
    emb = discord.Embed(title=f"{info} Bewerbung starten", description=desc, color=_color(settings))
    _footer(emb, settings)
    return emb
