from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from bot.core.perms import is_staff
from bot.modules.moderation.services.mod_service import ModerationService


async def _ephemeral(interaction: discord.Interaction, text: str):
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(text, ephemeral=True)
        else:
            await interaction.followup.send(text, ephemeral=True)
    except (discord.InteractionResponded, discord.NotFound, discord.HTTPException):
        try:
            await interaction.followup.send(text, ephemeral=True)
        except Exception:
            pass


async def _defer(interaction: discord.Interaction):
    try:
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True, thinking=True)
    except (discord.InteractionResponded, discord.NotFound, discord.HTTPException):
        pass


class ModerationCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = ModerationService(bot, bot.settings, bot.db, getattr(bot, "forum_logs", None))

    def _need_guild(self, interaction: discord.Interaction):
        return interaction.guild and isinstance(interaction.user, discord.Member)

    @app_commands.command(name="timeout", description="Timeout (Auto-Dauer wenn du keine angibst).")
    @app_commands.describe(user="User", minutes="Minuten (leer = Auto)", reason="Grund")
    async def timeout(self, interaction: discord.Interaction, user: discord.Member, minutes: int | None = None, reason: str | None = None):
        if not self._need_guild(interaction):
            return
        if not is_staff(self.bot.settings, interaction.user):
            return await _ephemeral(interaction, "Keine Rechte.")
        if not interaction.user.guild_permissions.moderate_members:
            return await _ephemeral(interaction, "Dir fehlt `Moderate Members`.")

        ok, err, used_minutes, strikes, case_id = await self.service.timeout(interaction.guild, interaction.user, user, minutes, reason)
        if not ok:
            return await _ephemeral(interaction, f"Timeout ging nicht: {err}")

        return await _ephemeral(interaction, f"Timeout gesetzt: **{used_minutes}min** (Strike **{strikes}**). Case: `{case_id}`")

    @app_commands.command(name="warn", description="Warnung vergeben.")
    @app_commands.describe(user="User", reason="Grund")
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str | None = None):
        if not self._need_guild(interaction):
            return
        if not is_staff(self.bot.settings, interaction.user):
            return await _ephemeral(interaction, "Keine Rechte.")
        if not interaction.user.guild_permissions.moderate_members:
            return await _ephemeral(interaction, "Dir fehlt `Moderate Members`.")

        strikes, case_id = await self.service.warn(interaction.guild, interaction.user, user, reason)
        return await _ephemeral(interaction, f"Warnung vergeben. Strikes jetzt: **{strikes}**. Case: `{case_id}`")

    @app_commands.command(name="kick", description="User kicken.")
    @app_commands.describe(user="User", reason="Grund")
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str | None = None):
        if not self._need_guild(interaction):
            return
        if not is_staff(self.bot.settings, interaction.user):
            return await _ephemeral(interaction, "Keine Rechte.")
        if not interaction.user.guild_permissions.kick_members:
            return await _ephemeral(interaction, "Dir fehlt `Kick Members`.")

        ok, err, case_id = await self.service.kick(interaction.guild, interaction.user, user, reason)
        if not ok:
            return await _ephemeral(interaction, f"Kick ging nicht: {err}")
        return await _ephemeral(interaction, f"{user.mention} wurde gekickt. Case: `{case_id}`")

    @app_commands.command(name="ban", description="User bannen.")
    @app_commands.describe(user="User", delete_days="Lösche Nachrichten der letzten X Tage (0-7)", reason="Grund")
    async def ban(self, interaction: discord.Interaction, user: discord.User, delete_days: int = 0, reason: str | None = None):
        if not self._need_guild(interaction):
            return
        if not is_staff(self.bot.settings, interaction.user):
            return await _ephemeral(interaction, "Keine Rechte.")
        if not interaction.user.guild_permissions.ban_members:
            return await _ephemeral(interaction, "Dir fehlt `Ban Members`.")

        ok, err, dd, case_id = await self.service.ban(interaction.guild, interaction.user, user, delete_days, reason)
        if not ok:
            return await _ephemeral(interaction, f"Ban ging nicht: {err}")
        return await _ephemeral(interaction, f"<@{user.id}> wurde gebannt. (delete_days={dd}) Case: `{case_id}`")

    @app_commands.command(name="purge", description="Nachrichten löschen.")
    @app_commands.describe(amount="Wie viele (1-100)", user="Optional: nur dieser User", reason="Optional: interner Grund")
    async def purge(self, interaction: discord.Interaction, amount: int, user: discord.Member | None = None, reason: str | None = None):
        if not self._need_guild(interaction):
            return
        if not is_staff(self.bot.settings, interaction.user):
            return await _ephemeral(interaction, "Keine Rechte.")
        if not interaction.user.guild_permissions.manage_messages:
            return await _ephemeral(interaction, "Dir fehlt `Manage Messages`.")

        if not isinstance(interaction.channel, discord.TextChannel):
            return await _ephemeral(interaction, "Nur in normalen Text-Channels.")

        await _defer(interaction)
        deleted, err, case_id = await self.service.purge(interaction.guild, interaction.user, interaction.channel, amount, user)
        if err:
            return await _ephemeral(interaction, f"Purge ging nicht: {err}")
        return await _ephemeral(interaction, f"Gelöscht: **{deleted}** Nachricht(en). Case: `{case_id}`")

    @app_commands.command(name="untimeout", description="Timeout entfernen.")
    @app_commands.describe(user="User", reason="Grund")
    async def untimeout(self, interaction: discord.Interaction, user: discord.Member, reason: str | None = None):
        if not self._need_guild(interaction):
            return
        if not is_staff(self.bot.settings, interaction.user):
            return await _ephemeral(interaction, "Keine Rechte.")
        if not interaction.user.guild_permissions.moderate_members:
            return await _ephemeral(interaction, "Dir fehlt `Moderate Members`.")
        try:
            await user.timeout(None, reason=reason or None)
        except Exception as e:
            return await _ephemeral(interaction, f"Timeout entfernen ging nicht: {type(e).__name__}: {e}")
        await _ephemeral(interaction, f"Timeout entfernt für {user.mention}.")

    @app_commands.command(name="unban", description="User entbannen.")
    @app_commands.describe(user_id="User-ID", reason="Grund")
    async def unban(self, interaction: discord.Interaction, user_id: int, reason: str | None = None):
        if not self._need_guild(interaction):
            return
        if not is_staff(self.bot.settings, interaction.user):
            return await _ephemeral(interaction, "Keine Rechte.")
        if not interaction.user.guild_permissions.ban_members:
            return await _ephemeral(interaction, "Dir fehlt `Ban Members`.")
        try:
            await interaction.guild.unban(discord.Object(id=int(user_id)), reason=reason or None)
        except Exception as e:
            return await _ephemeral(interaction, f"Unban ging nicht: {type(e).__name__}: {e}")
        await _ephemeral(interaction, f"<@{user_id}> wurde entbannt.")

    @app_commands.command(name="slowmode", description="Slowmode setzen.")
    @app_commands.describe(seconds="Sekunden (0-21600)")
    async def slowmode(self, interaction: discord.Interaction, seconds: int):
        if not self._need_guild(interaction):
            return
        if not is_staff(self.bot.settings, interaction.user):
            return await _ephemeral(interaction, "Keine Rechte.")
        if not interaction.user.guild_permissions.manage_channels:
            return await _ephemeral(interaction, "Dir fehlt `Manage Channels`.")
        if not isinstance(interaction.channel, discord.TextChannel):
            return await _ephemeral(interaction, "Nur in Text-Channels.")
        s = max(0, min(21600, int(seconds)))
        try:
            await interaction.channel.edit(slowmode_delay=s)
        except Exception as e:
            return await _ephemeral(interaction, f"Slowmode ging nicht: {type(e).__name__}: {e}")
        await _ephemeral(interaction, f"Slowmode gesetzt: **{s}s**.")

    @app_commands.command(name="lock", description="Channel sperren.")
    async def lock(self, interaction: discord.Interaction):
        if not self._need_guild(interaction):
            return
        if not is_staff(self.bot.settings, interaction.user):
            return await _ephemeral(interaction, "Keine Rechte.")
        if not interaction.user.guild_permissions.manage_channels:
            return await _ephemeral(interaction, "Dir fehlt `Manage Channels`.")
        if not isinstance(interaction.channel, discord.TextChannel):
            return await _ephemeral(interaction, "Nur in Text-Channels.")
        try:
            await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
        except Exception as e:
            return await _ephemeral(interaction, f"Lock ging nicht: {type(e).__name__}: {e}")
        await _ephemeral(interaction, "Channel gesperrt.")

    @app_commands.command(name="unlock", description="Channel entsperren.")
    async def unlock(self, interaction: discord.Interaction):
        if not self._need_guild(interaction):
            return
        if not is_staff(self.bot.settings, interaction.user):
            return await _ephemeral(interaction, "Keine Rechte.")
        if not interaction.user.guild_permissions.manage_channels:
            return await _ephemeral(interaction, "Dir fehlt `Manage Channels`.")
        if not isinstance(interaction.channel, discord.TextChannel):
            return await _ephemeral(interaction, "Nur in Text-Channels.")
        try:
            await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
        except Exception as e:
            return await _ephemeral(interaction, f"Unlock ging nicht: {type(e).__name__}: {e}")
        await _ephemeral(interaction, "Channel entsperrt.")

    @app_commands.command(name="nick", description="Nickname setzen.")
    @app_commands.describe(user="User", nickname="Neuer Nickname")
    async def nick(self, interaction: discord.Interaction, user: discord.Member, nickname: str | None = None):
        if not self._need_guild(interaction):
            return
        if not is_staff(self.bot.settings, interaction.user):
            return await _ephemeral(interaction, "Keine Rechte.")
        if not interaction.user.guild_permissions.manage_nicknames:
            return await _ephemeral(interaction, "Dir fehlt `Manage Nicknames`.")
        try:
            await user.edit(nick=nickname or None)
        except Exception as e:
            return await _ephemeral(interaction, f"Nick ging nicht: {type(e).__name__}: {e}")
        await _ephemeral(interaction, f"Nickname gesetzt für {user.mention}.")

    @app_commands.command(name="role-add", description="Rolle hinzufügen.")
    @app_commands.describe(user="User", role="Rolle")
    async def role_add(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role):
        if not self._need_guild(interaction):
            return
        if not is_staff(self.bot.settings, interaction.user):
            return await _ephemeral(interaction, "Keine Rechte.")
        if not interaction.user.guild_permissions.manage_roles:
            return await _ephemeral(interaction, "Dir fehlt `Manage Roles`.")
        try:
            await user.add_roles(role)
        except Exception as e:
            return await _ephemeral(interaction, f"Rolle hinzufügen ging nicht: {type(e).__name__}: {e}")
        await _ephemeral(interaction, f"{role.mention} zu {user.mention} hinzugefügt.")

    @app_commands.command(name="role-remove", description="Rolle entfernen.")
    @app_commands.describe(user="User", role="Rolle")
    async def role_remove(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role):
        if not self._need_guild(interaction):
            return
        if not is_staff(self.bot.settings, interaction.user):
            return await _ephemeral(interaction, "Keine Rechte.")
        if not interaction.user.guild_permissions.manage_roles:
            return await _ephemeral(interaction, "Dir fehlt `Manage Roles`.")
        try:
            await user.remove_roles(role)
        except Exception as e:
            return await _ephemeral(interaction, f"Rolle entfernen ging nicht: {type(e).__name__}: {e}")
        await _ephemeral(interaction, f"{role.mention} von {user.mention} entfernt.")

    @app_commands.command(name="softban", description="Softban (ban + unban).")
    @app_commands.describe(user="User", delete_days="Lösche Nachrichten der letzten X Tage (0-7)", reason="Grund")
    async def softban(self, interaction: discord.Interaction, user: discord.User, delete_days: int = 1, reason: str | None = None):
        if not self._need_guild(interaction):
            return
        if not is_staff(self.bot.settings, interaction.user):
            return await _ephemeral(interaction, "Keine Rechte.")
        if not interaction.user.guild_permissions.ban_members:
            return await _ephemeral(interaction, "Dir fehlt `Ban Members`.")
        ok, err, case_id = await self.service.softban(interaction.guild, interaction.user, user, delete_days, reason)
        if not ok:
            return await _ephemeral(interaction, f"Softban ging nicht: {err}")
        await _ephemeral(interaction, f"<@{user.id}> softbanned. Case: `{case_id}`")

    @app_commands.command(name="mass-timeout", description="Timeout für ganze Rolle.")
    @app_commands.describe(role="Zielrolle", minutes="Minuten", reason="Grund")
    async def mass_timeout(self, interaction: discord.Interaction, role: discord.Role, minutes: int, reason: str | None = None):
        if not self._need_guild(interaction):
            return
        if not is_staff(self.bot.settings, interaction.user):
            return await _ephemeral(interaction, "Keine Rechte.")
        if not interaction.user.guild_permissions.moderate_members:
            return await _ephemeral(interaction, "Dir fehlt `Moderate Members`.")
        await _defer(interaction)
        ok_count = 0
        fail_count = 0
        for member in role.members:
            ok, err, used, strikes, case_id = await self.service.timeout(interaction.guild, interaction.user, member, minutes, reason)
            if ok:
                ok_count += 1
            else:
                fail_count += 1
        await _ephemeral(interaction, f"Mass-Timeout fertig. OK: **{ok_count}**, Fehler: **{fail_count}**.")

    @app_commands.command(name="warns", description="Warn-History anzeigen.")
    @app_commands.describe(user="User", limit="Wie viele (max 20)")
    async def warns(self, interaction: discord.Interaction, user: discord.Member, limit: int = 10):
        if not self._need_guild(interaction):
            return
        if not is_staff(self.bot.settings, interaction.user):
            return await _ephemeral(interaction, "Keine Rechte.")
        n = max(1, min(20, int(limit)))
        rows = await self.bot.db.list_infractions(interaction.guild.id, user.id, limit=n)
        if not rows:
            return await _ephemeral(interaction, "Keine Einträge.")
        lines = []
        for r in rows:
            cid, action, dur, reason, created_at, mod_id = r
            if str(action) not in {"warn", "timeout"}:
                continue
            lines.append(f"• Case `{cid}` • {action} • {reason or '—'}")
        text = "\n".join(lines) if lines else "Keine Warns/Timeouts."
        await _ephemeral(interaction, text)

    @app_commands.command(name="case", description="Case anzeigen.")
    @app_commands.describe(case_id="Case-ID")
    async def case(self, interaction: discord.Interaction, case_id: int):
        if not self._need_guild(interaction):
            return
        if not is_staff(self.bot.settings, interaction.user):
            return await _ephemeral(interaction, "Keine Rechte.")
        row = await self.bot.db.get_infraction(interaction.guild.id, int(case_id))
        if not row:
            return await _ephemeral(interaction, "Case nicht gefunden.")
        cid, action, dur, reason, created_at, mod_id, user_id = row
        text = (
            f"┏`🆔` - Case: `{cid}`\n"
            f"┣`👤` - User: <@{user_id}>\n"
            f"┣`🧑‍⚖️` - Moderator: <@{mod_id}>\n"
            f"┣`⚙️` - Action: **{action}**\n"
            f"┣`⏳` - Dauer: **{dur or 0}**\n"
            f"┗`📝` - Grund: {reason or '—'}"
        )
        await _ephemeral(interaction, text)

    @app_commands.command(name="note", description="Mod-Notiz hinzufügen.")
    @app_commands.describe(user="User", note="Notiz")
    async def note(self, interaction: discord.Interaction, user: discord.Member, note: str):
        if not self._need_guild(interaction):
            return
        if not is_staff(self.bot.settings, interaction.user):
            return await _ephemeral(interaction, "Keine Rechte.")
        case_id = await self.service.add_note(interaction.guild, interaction.user, user, note)
        await _ephemeral(interaction, f"Notiz gespeichert. Case: `{case_id}`")

    @app_commands.command(name="notes", description="Mod-Notizen anzeigen.")
    @app_commands.describe(user="User", limit="Wie viele (max 20)")
    async def notes(self, interaction: discord.Interaction, user: discord.Member, limit: int = 10):
        if not self._need_guild(interaction):
            return
        if not is_staff(self.bot.settings, interaction.user):
            return await _ephemeral(interaction, "Keine Rechte.")
        n = max(1, min(20, int(limit)))
        rows = await self.bot.db.list_infractions(interaction.guild.id, user.id, limit=n)
        lines = []
        for r in rows:
            cid, action, dur, reason, created_at, mod_id = r
            if str(action) != "note":
                continue
            lines.append(f"• Case `{cid}` • {reason or '—'}")
        text = "\n".join(lines) if lines else "Keine Notizen."
        await _ephemeral(interaction, text)
