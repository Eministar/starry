import discord
from discord.utils import format_dt
from datetime import datetime
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


def build_summary_embed(
    settings,
    guild: discord.Guild | None,
    user: discord.User,
    member: discord.Member | None,
    category_label: str,
    created_at: datetime,
    total_tickets: int,
    priority: int | None = None,
    status_label: str | None = None,
    escalated_level: int | None = None,
):
    book = em(settings, "book", guild)
    arrow2 = em(settings, "arrow2", guild)

    joined = format_dt(member.joined_at, style="R") if member and member.joined_at else "unbekannt"

    desc = (
        f"{arrow2} Ich habe ein paar nützliche Details über diese Support-Anfrage zusammengetragen. 📝\n\n"
        f"┏`👥` - Profil: {user.mention} ({user.id})\n"
        f"┣`🌈` - Account erstellt: {format_dt(user.created_at, style='R')}\n"
        f"┣`🏆` - Server beigetreten: {joined}\n"
        f"┗`📬` - Hat bereits {total_tickets} Tickets erstellt.\n\n"
        f"┏`📚` - Ticket-Thema: {category_label}\n"
        f"┣`🚦` - Priorität: { _priority_label(priority) }\n"
        f"┣`🏷️` - Status: {status_label if status_label else 'offen'}\n"
        f"┣`⚠️` - Eskalation: {int(escalated_level) if escalated_level else 0}\n"
        f"┗`⏰` - Ticket erstellt: {format_dt(created_at, style='f')}\n\n"
        "Nutze die Buttons unten für Claim, Status, Priorität, Eskalation oder Transcript."
    )

    emb = discord.Embed(
        title=f"{book} 𑁉 SUPPORT-TICKET - ZUSAMMENFASSUNG",
        description=desc,
        color=_color(settings),
    )
    emb.set_thumbnail(url=user.display_avatar.url)
    _footer(emb, settings)
    return emb


def _priority_label(priority: int | None) -> str:
    mapping = {
        1: "Niedrig",
        2: "Normal",
        3: "Hoch",
        4: "Dringend",
    }
    try:
        return mapping.get(int(priority or 2), "Normal")
    except Exception:
        return "Normal"


def build_user_message_embed(settings, guild: discord.Guild | None, user: discord.User, content: str):
    arrow2 = em(settings, "arrow2", guild)
    desc = f"{arrow2} {content}" if content else f"{arrow2} "
    emb = discord.Embed(description=desc, color=_color(settings))
    emb.set_author(name=user.display_name, icon_url=user.display_avatar.url)
    _footer(emb, settings)
    return emb


def build_dm_ticket_created_embed(settings, guild: discord.Guild | None, ticket_id: int, created_at: datetime):
    book = em(settings, "book", guild)
    arrow2 = em(settings, "arrow2", guild)
    green = em(settings, "green", guild)

    desc = (
        f"{arrow2} Dein Ticket wurde erstellt – unser Team antwortet dir hier per DM.\n\n"
        f"┏`📚` - Ticket-ID: `{ticket_id}`\n"
        f"┣`⏰` - Erstellt: {format_dt(created_at, style='f')}\n"
        f"┗`🟢` - Status: Offen\n\n"
        f"Schreib einfach hier weiter, ich häng’s automatisch ans Ticket."
    )

    emb = discord.Embed(
        title=f"{book} 𑁉 SUPPORT-TICKET - BESTÄTIGUNG",
        description=desc,
        color=_color(settings),
    )
    _footer(emb, settings)
    return emb


def build_dm_message_appended_embed(settings, guild: discord.Guild | None, ticket_id: int):
    arrow2 = em(settings, "arrow2", guild)
    info = em(settings, "info", guild)

    desc = (
        f"{arrow2} Hab’s ans Ticket gehängt.\n\n"
        f"┏`📚` - Ticket-ID: `{ticket_id}`\n"
        f"┗`✅` - Info: Du bekommst Antworten vom Team hier per DM."
    )

    emb = discord.Embed(
        title=f"{info} 𑁉 NACHRICHT ÜBERNOMMEN",
        description=desc,
        color=_color(settings),
    )
    _footer(emb, settings)
    return emb


def build_dm_staff_reply_embed(settings, guild: discord.Guild | None, staff: discord.Member, ticket_id: int, text: str):
    love = em(settings, "discord_love", guild)
    arrow2 = em(settings, "arrow2", guild)

    desc = (
        f"{arrow2} {text if text else ' '}\n\n"
        f"┏`👤` - Teamer: **{staff.display_name}**\n"
        f"┗`📚` - Ticket-ID: `{ticket_id}`"
    )

    emb = discord.Embed(
        title=f"{love} 𑁉 TEAM-ANTWORT",
        description=desc,
        color=_color(settings),
    )
    emb.set_author(name=staff.display_name, icon_url=staff.display_avatar.url)
    _footer(emb, settings)
    return emb


def build_dm_ticket_closed_embed(settings, guild: discord.Guild | None, ticket_id: int, closed_at: datetime, rating_enabled: bool):
    red = em(settings, "red", guild)
    arrow2 = em(settings, "arrow2", guild)

    tail = "Bewerte den Support unten mit ⭐." if rating_enabled else "Wenn du nochmal was brauchst, schreib einfach neu."
    desc = (
        f"{arrow2} Ticket ist zu. Danke dir! 💜\n\n"
        f"┏`📚` - Ticket-ID: `{ticket_id}`\n"
        f"┗`⏰` - Geschlossen: {format_dt(closed_at, style='f')}\n\n"
        f"{tail}"
    )

    emb = discord.Embed(
        title=f"{red} 𑁉 TICKET GESCHLOSSEN",
        description=desc,
        color=_color(settings),
    )
    _footer(emb, settings)
    return emb


def build_dm_rating_thanks_embed(settings, guild: discord.Guild | None, rating: int):
    cheers = em(settings, "cheers", guild)
    arrow2 = em(settings, "arrow2", guild)

    desc = (
        f"{arrow2} Danke für deine Bewertung! 💜\n\n"
        f"┏`⭐` - Bewertung: **{rating}/5**\n"
        f"┗`📌` - Info: Hilft uns extrem, den Support besser zu machen."
    )

    emb = discord.Embed(
        title=f"{cheers} 𑁉 BEWERTUNG GESPEICHERT",
        description=desc,
        color=_color(settings),
    )
    _footer(emb, settings)
    return emb


def build_dm_ticket_added_embed(settings, guild: discord.Guild | None, ticket_id: int, added_by: discord.Member):
    info = em(settings, "info", guild)
    arrow2 = em(settings, "arrow2", guild)
    desc = (
        f"{arrow2} Du wurdest zu einem Ticket hinzugefügt.\n\n"
        f"• Ticket-ID: `{ticket_id}`\n"
        f"• Hinzugefügt von: **{added_by.display_name}**\n\n"
        f"Schreib einfach hier, deine Nachricht landet im Ticket."
    )
    emb = discord.Embed(
        title=f"{info} TICKET-ZUGANG",
        description=desc,
        color=_color(settings),
    )
    _footer(emb, settings)
    return emb


def build_thread_status_embed(settings, guild: discord.Guild | None, title: str, text: str, actor: discord.Member | None = None):
    arrow2 = em(settings, "arrow2", guild)
    emb = discord.Embed(
        title=title,
        description=f"{arrow2} {text}",
        color=_color(settings),
    )
    if actor:
        emb.set_author(name=actor.display_name, icon_url=actor.display_avatar.url)
    _footer(emb, settings)
    return emb


def build_thread_rating_embed(settings, guild: discord.Guild | None, user_id: int, rating: int, comment: str | None):
    hearts = em(settings, "hearts", guild)

    desc = f"┏`⭐` - Bewertung: **{rating}/5**\n┗`👤` - User: <@{user_id}>"
    if comment:
        desc += f"\n\n{comment}"

    emb = discord.Embed(
        title=f"{hearts} 𑁉 BEWERTUNG",
        description=desc,
        color=_color(settings),
    )
    _footer(emb, settings)
    return emb


def build_dm_ticket_update_embed(settings, guild: discord.Guild | None, title: str, text: str):
    info = em(settings, "info", guild) or "ℹ️"
    arrow2 = em(settings, "arrow2", guild) or "»"
    desc = f"{arrow2} {text}"
    emb = discord.Embed(
        title=f"{info} 𑁉 {title}",
        description=desc,
        color=_color(settings),
    )
    _footer(emb, settings)
    return emb


def build_dm_ticket_forwarded_embed(
    settings,
    guild: discord.Guild | None,
    role_name: str,
    reason: str | None,
):
    info = em(settings, "info", guild) or "ℹ️"
    arrow2 = em(settings, "arrow2", guild) or "»"
    reason_text = reason or "—"
    desc = (
        f"{arrow2} Ich habe dein Ticket weitergeleitet, damit dir die richtige Person helfen kann.\n\n"
        f"┏`🎯` - Ziel: **{role_name}**\n"
        f"┗`📝` - Grund: {reason_text}\n\n"
        "Sobald jemand verfügbar ist, meldet sich das Team bei dir."
    )
    emb = discord.Embed(
        title=f"{info} 𑁉 TICKET WEITERGELEITET",
        description=desc,
        color=_color(settings),
    )
    _footer(emb, settings)
    return emb


def build_ticket_log_embed(
    settings,
    guild: discord.Guild | None,
    title: str,
    text: str,
    ticket_id: int,
    thread: discord.Thread | None = None,
    actor: discord.Member | None = None,
):
    info = em(settings, "info", guild) or "ℹ️"
    arrow2 = em(settings, "arrow2", guild) or "»"
    thread_line = f"{thread.mention} ({thread.id})" if thread else "—"
    actor_line = f"{actor.mention} ({actor.id})" if actor else "—"
    desc = (
        f"┏`🎫` - Ticket: `{int(ticket_id)}`\n"
        f"┣`🧵` - Thread: {thread_line}\n"
        f"┣`👤` - Actor: {actor_line}\n"
        f"┗`📝` - Info: {text}"
    )
    emb = discord.Embed(
        title=f"{info} 𑁉 {title}",
        description=f"{arrow2} Ticket-Event\n\n{desc}",
        color=_color(settings),
    )
    _footer(emb, settings)
    return emb
