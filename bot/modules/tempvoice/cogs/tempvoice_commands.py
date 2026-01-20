import discord
from discord import app_commands
from discord.ext import commands
from bot.modules.tempvoice.services.tempvoice_service import TempVoiceService


class TempVoiceCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = getattr(bot, "tempvoice_service", None) or TempVoiceService(
            bot, bot.settings, bot.db, bot.logger
        )

    tempvoice = app_commands.Group(name="tempvoice", description="🎙️ 𑁉 Temp-Voice-Tools")

    @tempvoice.command(name="panel", description="🎛️ 𑁉 Temp-Voice Panel senden")
    async def panel(self, interaction: discord.Interaction):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Nur im Server nutzbar.", ephemeral=True)
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("Du bist in keinem Voice.", ephemeral=True)
        channel = interaction.user.voice.channel
        if not isinstance(channel, discord.VoiceChannel):
            return await interaction.response.send_message("Kein Voice-Channel.", ephemeral=True)
        await self.service.send_panel_for_channel(interaction, channel.id)
