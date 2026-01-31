import discord
from discord.ext import commands

from bot.modules.invites.services.invite_service import InviteService


class InviteListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = getattr(bot, "invite_service", None) or InviteService(bot, bot.settings, bot.db, bot.logger)

    @commands.Cog.listener("on_ready")
    async def on_ready(self):
        for guild in list(self.bot.guilds):
            try:
                await self.service.seed_cache(guild)
            except Exception:
                continue

    @commands.Cog.listener("on_invite_create")
    async def on_invite_create(self, invite: discord.Invite):
        await self.service.on_invite_create(invite)

    @commands.Cog.listener("on_invite_delete")
    async def on_invite_delete(self, invite: discord.Invite):
        await self.service.on_invite_delete(invite)

    @commands.Cog.listener("on_member_join")
    async def on_member_join(self, member: discord.Member):
        await self.service.on_member_join(member)

    @commands.Cog.listener("on_member_remove")
    async def on_member_remove(self, member: discord.Member):
        await self.service.on_member_remove(member)
