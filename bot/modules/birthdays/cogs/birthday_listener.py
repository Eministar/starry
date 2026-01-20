import discord
from discord.ext import commands
from bot.modules.birthdays.services.birthday_service import BirthdayService


class BirthdayListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = getattr(bot, "birthday_service", None) or BirthdayService(bot, bot.settings, bot.db, bot.logger)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild:
            return
        if not self.bot.settings.get_guild_bool(message.guild.id, "birthday.enabled", True):
            return
        await self.service.auto_react(message)
