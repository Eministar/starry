import discord
from discord import app_commands
from discord.ext import commands


class RolesCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    roles = app_commands.Group(name="roles", description="🧩 𑁉 Rollen-Tools")

    @roles.command(name="sync", description="🔄 𑁉 Auto-Rollen syncen")
    async def sync(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("Nur im Server nutzbar.", ephemeral=True)
        await interaction.response.send_message("Rollen-Sync läuft…", ephemeral=True)
        try:
            if getattr(self.bot, "user_stats_service", None):
                await self.bot.user_stats_service.ensure_roles(interaction.guild)
            if getattr(self.bot, "birthday_service", None):
                await self.bot.birthday_service.ensure_roles(interaction.guild)
            await interaction.followup.send("Rollen-Sync abgeschlossen.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Rollen-Sync fehlgeschlagen: `{type(e).__name__}`", ephemeral=True)
