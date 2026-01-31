import discord
from discord import app_commands
from discord.ext import commands

from bot.core.perms import is_staff
from bot.modules.seelsorge.services.seelsorge_service import SeelsorgeService


class SeelsorgeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = getattr(bot, "seelsorge_service", None) or SeelsorgeService(bot, bot.settings, bot.db, bot.logger)

    seelsorge = app_commands.Group(name="seelsorge", description="🧠 𑁉 Seelsorge")

    @seelsorge.command(name="setup", description="⚙️ 𑁉 Seelsorge konfigurieren")
    @app_commands.describe(forum="Forum-Channel für Seelsorge")
    async def setup(self, interaction: discord.Interaction, forum: discord.ForumChannel):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Nur im Server nutzbar.", ephemeral=True)
        if not is_staff(self.bot.settings, interaction.user):
            return await interaction.response.send_message("Keine Rechte.", ephemeral=True)
        await self.service.configure(interaction.guild, forum)
        await interaction.response.send_message("Konfiguration gespeichert.", ephemeral=True)

    @seelsorge.command(name="panel", description="📌 𑁉 Panel im Forum senden")
    @app_commands.describe(forum="Optional: Forum-Channel überschreiben")
    async def panel(self, interaction: discord.Interaction, forum: discord.ForumChannel | None = None):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Nur im Server nutzbar.", ephemeral=True)
        if not is_staff(self.bot.settings, interaction.user):
            return await interaction.response.send_message("Keine Rechte.", ephemeral=True)
        await self.service.send_panel(interaction, forum)
