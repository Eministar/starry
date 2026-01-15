import discord
from discord import app_commands
from discord.ext import commands
from bot.modules.birthdays.services.birthday_service import BirthdayService


class BirthdayCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = getattr(bot, "birthday_service", None) or BirthdayService(bot, bot.settings, bot.db, bot.logger)

    birthday = app_commands.Group(name="birthday", description="Geburtstage verwalten")

    @birthday.command(name="set", description="Geburtstag setzen")
    @app_commands.describe(day="Tag", month="Monat", year="Jahr")
    async def set_birthday(self, interaction: discord.Interaction, day: int, month: int, year: int):
        await self.service.set_birthday(interaction, day, month, year)

    @birthday.command(name="remove", description="Geburtstag entfernen")
    async def remove_birthday(self, interaction: discord.Interaction):
        await self.service.remove_birthday(interaction)

    @birthday.command(name="show", description="Geburtstag anzeigen")
    @app_commands.describe(user="Optionaler User")
    async def show_birthday(self, interaction: discord.Interaction, user: discord.Member | None = None):
        await self.service.show_birthday(interaction, user=user)

    @birthday.command(name="list", description="Geburtstagsliste anzeigen")
    async def list_birthdays(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("Nur im Server nutzbar.", ephemeral=True)
        emb, page, total_pages = await self.service.build_birthday_list_embed(interaction.guild, page=1, per_page=10)
        view = BirthdayListView(self.service, interaction.guild, page, total_pages)
        await interaction.response.send_message(embed=emb, view=view, ephemeral=True)


class BirthdayListView(discord.ui.View):
    def __init__(self, service: BirthdayService, guild: discord.Guild, page: int, total_pages: int):
        super().__init__(timeout=120)
        self.service = service
        self.guild = guild
        self.page = page
        self.total_pages = total_pages
        self._update_buttons()

    def _update_buttons(self):
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item.custom_id == "birthday_prev":
                    item.disabled = self.page <= 1
                if item.custom_id == "birthday_next":
                    item.disabled = self.page >= self.total_pages

    @discord.ui.button(label="Zurück", style=discord.ButtonStyle.secondary, custom_id="birthday_prev")
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = max(1, self.page - 1)
        emb, page, total_pages = await self.service.build_birthday_list_embed(self.guild, page=self.page, per_page=10)
        self.page = page
        self.total_pages = total_pages
        self._update_buttons()
        await interaction.response.edit_message(embed=emb, view=self)

    @discord.ui.button(label="Weiter", style=discord.ButtonStyle.primary, custom_id="birthday_next")
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = min(self.total_pages, self.page + 1)
        emb, page, total_pages = await self.service.build_birthday_list_embed(self.guild, page=self.page, per_page=10)
        self.page = page
        self.total_pages = total_pages
        self._update_buttons()
        await interaction.response.edit_message(embed=emb, view=self)
