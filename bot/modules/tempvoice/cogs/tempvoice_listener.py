import discord
from discord.ext import commands
from bot.modules.tempvoice.services.tempvoice_service import TempVoiceService


class TempVoiceListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = getattr(bot, "tempvoice_service", None) or TempVoiceService(
            bot, bot.settings, bot.db, bot.logger
        )

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        await self.service.handle_voice_state_update(member, before, after)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        if isinstance(channel, discord.VoiceChannel):
            await self.service.handle_channel_delete(channel.guild, channel.id)
