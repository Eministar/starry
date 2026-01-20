from __future__ import annotations

import discord
from discord.ext import commands

from bot.modules.logs.formatting.log_embeds import (
    build_message_edited_embed,
    build_message_deleted_embed,
    build_join_embed,
    build_leave_embed,
)


class ModLogListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if not member.guild:
            return
        logs = getattr(self.bot, "forum_logs", None)
        if not logs:
            return
        emb = build_join_embed(self.bot.settings, member.guild, member)
        await logs.emit(member.guild, "join_leave", emb)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if not member.guild:
            return
        logs = getattr(self.bot, "forum_logs", None)
        if not logs:
            return
        emb = build_leave_embed(self.bot.settings, member.guild, member)
        await logs.emit(member.guild, "join_leave", emb)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if not after.guild:
            return
        if not before.content and not after.content:
            return
        if before.content == after.content:
            return
        if after.author and after.author.bot:
            return
        logs = getattr(self.bot, "forum_logs", None)
        if not logs:
            return

        author = after.author if isinstance(after.author, discord.Member) else None
        emb = build_message_edited_embed(self.bot.settings, after.guild, author, after.channel, before.content or "", after.content or "", after.id)
        await logs.emit(after.guild, "message_updates", emb)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message.guild:
            return
        if message.author and message.author.bot:
            return
        logs = getattr(self.bot, "forum_logs", None)
        if not logs:
            return

        author = message.author if isinstance(message.author, discord.Member) else None
        content = message.content or ""
        emb = build_message_deleted_embed(self.bot.settings, message.guild, author, message.channel, content, message.id)
        await logs.emit(message.guild, "message_updates", emb)
