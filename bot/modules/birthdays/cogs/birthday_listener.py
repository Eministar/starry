import discord
from discord.ext import commands
from bot.modules.birthdays.services.birthday_service import BirthdayService


class BirthdayListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = getattr(bot, "birthday_service", None) or BirthdayService(bot, bot.settings, bot.db, bot.logger)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not self.bot.settings.get_bool("birthday.enabled", True):
            return
        await self.service.auto_react(message)
