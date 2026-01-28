import discord
from discord import app_commands
from discord.ext import commands

from bot.core.perms import is_staff
from bot.modules.news.services.news_service import NewsService


class NewsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = getattr(bot, "news_service", None) or NewsService(bot, bot.settings, bot.db, bot.logger)

    news = app_commands.Group(name="news", description="📰 𑁉 News-Tools")
    youtube = app_commands.Group(name="youtube", description="📺 𑁉 YouTube-News")

    @news.command(name="send", description="📰 𑁉 Neueste Tagesschau-News senden")
    async def send(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("Nur im Server nutzbar.", ephemeral=True)
        if not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Nur im Server nutzbar.", ephemeral=True)
        if not is_staff(self.bot.settings, interaction.user):
            return await interaction.response.send_message("Keine Berechtigung.", ephemeral=True)

        await interaction.response.send_message("News wird gesendet...", ephemeral=True)
        ok, err = await self.service.send_latest_news(interaction.guild, force=True)
        if ok:
            await interaction.followup.send("News gesendet.", ephemeral=True)
        elif err:
            await interaction.followup.send(err, ephemeral=True)
        else:
            await interaction.followup.send("Keine neuen News.", ephemeral=True)

    @youtube.command(name="send", description="📺 𑁉 Neuestes Video einer Quelle senden")
    @app_commands.describe(channel="Handle/Name/Channel-ID aus config (z.B. papaplatte)")
    async def youtube_send(self, interaction: discord.Interaction, channel: str):
        if not interaction.guild:
            return await interaction.response.send_message("Nur im Server nutzbar.", ephemeral=True)
        if not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Nur im Server nutzbar.", ephemeral=True)
        if not is_staff(self.bot.settings, interaction.user):
            return await interaction.response.send_message("Keine Berechtigung.", ephemeral=True)

        await interaction.response.send_message("YouTube-Video wird gesendet...", ephemeral=True)
        ok, err = await self.service.send_latest_youtube(interaction.guild, channel)
        if ok:
            await interaction.followup.send("Video gesendet.", ephemeral=True)
        elif err:
            await interaction.followup.send(err, ephemeral=True)
        else:
            await interaction.followup.send("Kein Video gefunden.", ephemeral=True)
