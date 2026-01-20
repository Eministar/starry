import discord
from discord.ext import commands
from bot.modules.tickets.services.ticket_service import TicketService


class TicketForumListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = getattr(bot, "ticket_service", None) or TicketService(bot, bot.settings, bot.db, bot.logger)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild:
            return
        if message.author.bot:
            return
        if not isinstance(message.channel, discord.Thread):
            return
        forum_id = self.bot.settings.get_guild_int(message.guild.id, "bot.forum_channel_id")
        parent = getattr(message.channel, "parent", None)
        if not parent or getattr(parent, "id", 0) != forum_id:
            return
        await self.service.handle_staff_message(message)
