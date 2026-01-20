import discord
from discord import app_commands
from discord.ext import commands
from bot.modules.user_stats.services.user_stats_service import UserStatsService


class UserStatsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = getattr(bot, "user_stats_service", None) or UserStatsService(bot, bot.settings, bot.db, bot.logger)

    @app_commands.command(name="me", description="📊 𑁉 Deine User-Statistiken")
    async def me(self, interaction: discord.Interaction):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Nur im Server nutzbar.", ephemeral=True)
        emb = await self.service.build_me_embed(interaction.user)
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @app_commands.command(name="ich", description="📊 𑁉 Deine User-Statistiken")
    async def ich(self, interaction: discord.Interaction):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Nur im Server nutzbar.", ephemeral=True)
        emb = await self.service.build_me_embed(interaction.user)
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @app_commands.command(name="erfolge", description="🏆 𑁉 Deine Erfolge")
    async def erfolge(self, interaction: discord.Interaction):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Nur im Server nutzbar.", ephemeral=True)
        emb, page, total_pages = await self.service.build_achievements_embed(interaction.user, page=1, per_page=8)
        view = AchievementsView(self.service, interaction.user, page, total_pages)
        await interaction.response.send_message(embed=emb, view=view, ephemeral=True)


class AchievementsView(discord.ui.View):
    def __init__(self, service: UserStatsService, member: discord.Member, page: int, total_pages: int):
        super().__init__(timeout=120)
        self.service = service
        self.member = member
        self.page = page
        self.total_pages = total_pages
        self._update_buttons()

    def _update_buttons(self):
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item.custom_id == "ach_prev":
                    item.disabled = self.page <= 1
                if item.custom_id == "ach_next":
                    item.disabled = self.page >= self.total_pages

    @discord.ui.button(label="Zurück", style=discord.ButtonStyle.secondary, custom_id="ach_prev")
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = max(1, self.page - 1)
        emb, page, total_pages = await self.service.build_achievements_embed(self.member, page=self.page, per_page=8)
        self.page = page
        self.total_pages = total_pages
        self._update_buttons()
        await interaction.response.edit_message(embed=emb, view=self)

    @discord.ui.button(label="Weiter", style=discord.ButtonStyle.primary, custom_id="ach_next")
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = min(self.total_pages, self.page + 1)
        emb, page, total_pages = await self.service.build_achievements_embed(self.member, page=self.page, per_page=8)
        self.page = page
        self.total_pages = total_pages
        self._update_buttons()
        await interaction.response.edit_message(embed=emb, view=self)
