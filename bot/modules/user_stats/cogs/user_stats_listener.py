import discord
from discord.ext import commands
from bot.modules.user_stats.services.user_stats_service import UserStatsService


class UserStatsListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = getattr(bot, "user_stats_service", None) or UserStatsService(bot, bot.settings, bot.db, bot.logger)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not self.bot.settings.get_bool("user_stats.enabled", True):
            return
        await self.service.on_message(message)

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        if not self.bot.settings.get_bool("user_stats.enabled", True):
            return
        await self.service.on_presence_update(before, after)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if not self.bot.settings.get_bool("user_stats.enabled", True):
            return
        await self.service.on_member_update(before, after)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if not self.bot.settings.get_bool("user_stats.enabled", True):
            return
        await self.service.on_voice_state_update(member, before, after)
