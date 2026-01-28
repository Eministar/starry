import discord
from discord import app_commands
from discord.ext import commands

from bot.core.perms import is_staff
from bot.modules.wort_zum_sonntag.services.wort_service import WortZumSonntagService


class WortCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = getattr(bot, "wzs_service", None) or WortZumSonntagService(bot, bot.settings, bot.db, bot.logger)

    wort = app_commands.Group(name="wort", description="📖 𑁉 Wort-zum-Sonntag")

    @wort.command(name="setup", description="⚙️ 𑁉 Wort-zum-Sonntag konfigurieren")
    @app_commands.describe(
        forum="Forum-Channel für Einsendungen",
        review_role="Rolle für Annahme/Ablehnung",
        ping_role="Rolle für Ping-Benachrichtigungen",
    )
    async def setup(
        self,
        interaction: discord.Interaction,
        forum: discord.ForumChannel,
        review_role: discord.Role | None = None,
        ping_role: discord.Role | None = None,
    ):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Nur im Server nutzbar.", ephemeral=True)
        if not is_staff(self.bot.settings, interaction.user):
            return await interaction.response.send_message("Keine Rechte.", ephemeral=True)
        await self.service.configure(interaction.guild, forum, review_role, ping_role)
        await interaction.response.send_message("Konfiguration gespeichert.", ephemeral=True)

    @wort.command(name="panel", description="📌 𑁉 Panel im Forum senden")
    @app_commands.describe(forum="Optional: Forum-Channel überschreiben")
    async def panel(self, interaction: discord.Interaction, forum: discord.ForumChannel | None = None):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Nur im Server nutzbar.", ephemeral=True)
        if not is_staff(self.bot.settings, interaction.user):
            return await interaction.response.send_message("Keine Rechte.", ephemeral=True)
        await self.service.send_panel(interaction, forum)

    @wort.command(name="annehmen", description="✅ 𑁉 Weisheit annehmen")
    async def accept(self, interaction: discord.Interaction):
        await self.service.set_status(interaction, "accepted")

    @wort.command(name="ablehnen", description="⛔ 𑁉 Weisheit ablehnen")
    async def reject(self, interaction: discord.Interaction):
        await self.service.set_status(interaction, "rejected")
