import discord
from discord.ext import commands
from bot.modules.giveaways.services.giveaway_service import GiveawayService


class GiveawayListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = getattr(bot, "giveaway_service", None) or GiveawayService(bot, bot.settings, bot.db, bot.logger)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return
        if not self.bot.settings.get_bool("giveaway.enabled", True):
            return
        if not payload.guild_id:
            return
        row = await self.bot.db.get_giveaway_by_message(payload.guild_id, payload.message_id)
        if not row:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        join_emoji = self.service._join_emoji(guild)
        emoji_str = str(payload.emoji)
        if emoji_str != join_emoji:
            return
        member = guild.get_member(payload.user_id)
        if not member:
            try:
                member = await guild.fetch_member(payload.user_id)
            except Exception:
                member = None
        if not member:
            return
        channel = guild.get_channel(payload.channel_id)
        if not channel:
            try:
                channel = await self.bot.fetch_channel(payload.channel_id)
            except Exception:
                channel = None
        if not channel:
            return
        try:
            msg = await channel.fetch_message(payload.message_id)
        except Exception:
            msg = None
        interaction = _FakeInteraction(self.bot, guild, member, msg)
        await self.service.handle_join(interaction, int(row[0]))


class _FakeInteraction:
    def __init__(self, bot, guild: discord.Guild, user: discord.Member, message: discord.Message | None):
        self.guild = guild
        self.user = user
        self.message = message
        self.client = bot

    @property
    def response(self):
        return _FakeResponse()


class _FakeResponse:
    async def send_message(self, *args, **kwargs):
        return None
