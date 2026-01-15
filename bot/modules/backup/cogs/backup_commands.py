import discord
from discord import app_commands
from discord.ext import commands
from bot.modules.backup.services.backup_service import BackupService


class BackupCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = getattr(bot, "backup_service", None) or BackupService(bot, bot.settings, bot.db, bot.logger)

    backup = app_commands.Group(name="backup", description="Backup-Tools")

    @backup.command(name="save", description="Backup speichern")
    @app_commands.describe(name="Optionaler Name des Backups")
    async def save(self, interaction: discord.Interaction, name: str | None = None):
        if not interaction.guild:
            return await interaction.response.send_message("Nur im Server nutzbar.", ephemeral=True)
        await interaction.response.send_message("Backup wird gespeichert…", ephemeral=True)
        backup_id, backup_name = await self.service.create_backup(interaction.guild, name=name)
        await interaction.followup.send(f"Backup gespeichert: `{backup_name}` (ID {backup_id})", ephemeral=True)

    @backup.command(name="load", description="Backup wiederherstellen")
    @app_commands.describe(name="Backup-Name oder 'latest'")
    async def load(self, interaction: discord.Interaction, name: str = "latest"):
        if not interaction.guild:
            return await interaction.response.send_message("Nur im Server nutzbar.", ephemeral=True)
        await interaction.response.send_message("Backup wird geladen…", ephemeral=True)
        if name == "latest":
            row = await self.bot.db.get_latest_backup(interaction.guild.id)
        else:
            row = await self.bot.db.get_backup_by_name(interaction.guild.id, name)
        ok, err = await self.service.load_backup(interaction.guild, row, name=name)
        if not ok:
            return await interaction.followup.send(f"Backup fehlgeschlagen: `{err}`", ephemeral=True)
        await interaction.followup.send("Backup geladen und synchronisiert.", ephemeral=True)

    @backup.command(name="list", description="Backups auflisten")
    async def list(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("Nur im Server nutzbar.", ephemeral=True)
        rows = await self.bot.db.list_backups(interaction.guild.id, limit=20)
        if not rows:
            return await interaction.response.send_message("Keine Backups vorhanden.", ephemeral=True)
        lines = [f"`{r[0]}` • {r[1]} • {r[2]}" for r in rows]
        text = "\n".join(lines)
        emb = discord.Embed(title="💾 𑁉 BACKUPS", description=text, color=0xB16B91)
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @backup.command(name="diff", description="Zeigt Unterschiede zum Backup")
    @app_commands.describe(name="Backup-Name oder 'latest'")
    async def diff(self, interaction: discord.Interaction, name: str = "latest"):
        if not interaction.guild:
            return await interaction.response.send_message("Nur im Server nutzbar.", ephemeral=True)
        if name == "latest":
            row = await self.bot.db.get_latest_backup(interaction.guild.id)
        else:
            row = await self.bot.db.get_backup_by_name(interaction.guild.id, name)
        diff = await self.service.diff_backup(interaction.guild, row)
        if not diff:
            return await interaction.response.send_message("Backup nicht gefunden oder ungültig.", ephemeral=True)
        desc = (
            f"┏`🧩` - Rollen neu: **{diff['roles_missing']}**, Updates: **{diff['roles_update']}**\n"
            f"┣`📁` - Channels neu: **{diff['channels_missing']}**, Updates: **{diff['channels_update']}**\n"
            f"┣`🔐` - Permissions Sync: **{diff['permissions_update']}**\n"
            f"┣`👥` - Member-Rollen abweichend: **{diff['member_roles_changes']}**\n"
            f"┣`😄` - Emojis neu: **{diff['emojis_missing']}**, Updates: **{diff['emojis_update']}**\n"
            f"┣`🧷` - Sticker neu: **{diff['stickers_missing']}**, Updates: **{diff['stickers_update']}**\n"
            f"┗`🔗` - Webhooks neu: **{diff['webhooks_missing']}**, Updates: **{diff['webhooks_update']}**"
        )
        emb = discord.Embed(title="🧭 𑁉 BACKUP-DIFF", description=desc, color=0xB16B91)
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @backup.command(name="autosave", description="Auto-Backup aktivieren/deaktivieren")
    @app_commands.describe(enabled="True/False")
    async def autosave(self, interaction: discord.Interaction, enabled: bool):
        await self.bot.settings.set_override("backup.auto_save_enabled", bool(enabled))
        await interaction.response.send_message(f"Auto-Save {'aktiviert' if enabled else 'deaktiviert'}.", ephemeral=True)
