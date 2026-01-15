import discord
from bot.modules.applications.formatting.application_embeds import build_application_embed, build_application_dm_embed


class ApplicationService:
    def __init__(self, bot: discord.Client, settings, db, logger):
        self.bot = bot
        self.settings = settings
        self.db = db
        self.logger = logger
        self._sessions: dict[int, dict] = {}

    def _config(self) -> dict:
        return self.settings.get("applications", {}) or {}

    def _questions(self) -> list[str]:
        cfg = self._config()
        q = cfg.get("questions", [])
        if isinstance(q, list) and q:
            return [str(x) for x in q][:5]
        return [
            "Warum möchtest du dich bewerben?",
            "Wie viel Erfahrung hast du?",
            "Wie alt bist du?",
            "Was sind deine Stärken?",
            "Wann hast du Zeit?",
        ]

    async def has_open_ticket(self, guild_id: int, user_id: int) -> bool:
        try:
            row = await self.db.get_open_ticket_by_user(int(guild_id), int(user_id))
            if row:
                return True
            row2 = await self.db.get_open_ticket_by_participant(int(guild_id), int(user_id))
            return bool(row2)
        except Exception:
            return False

    async def start_dm_flow(self, user: discord.User, guild: discord.Guild | None):
        questions = self._questions()
        self._sessions[user.id] = {"idx": 0, "answers": [], "questions": questions, "guild_id": int(guild.id) if guild else 0}
        emb = build_application_dm_embed(self.settings, guild, questions)
        try:
            await user.send(embed=emb)
            await user.send(f"1/{len(questions)}: {questions[0]}")
        except Exception:
            pass
        return questions

    async def handle_dm_answer(self, message: discord.Message):
        if message.author.bot:
            return
        sess = self._sessions.get(int(message.author.id))
        if not sess:
            return
        text = (message.content or "").strip()
        if not text:
            return
        sess["answers"].append(text)
        sess["idx"] += 1
        idx = int(sess["idx"])
        questions = sess["questions"]
        if idx >= len(questions):
            guild_id = int(sess.get("guild_id") or 0)
            guild = self.bot.get_guild(guild_id) if guild_id else None
            if not guild and guild_id:
                try:
                    guild = await self.bot.fetch_guild(guild_id)
                except Exception:
                    guild = None
            if guild:
                try:
                    interaction = _FakeInteraction(guild, message.author)
                    await self.start_application(interaction, sess["answers"])
                    await message.author.send("✅ Bewerbung wurde eingereicht. Danke!")
                except Exception:
                    await message.author.send("⚠️ Bewerbung konnte nicht eingereicht werden.")
            else:
                await message.author.send("⚠️ Server nicht gefunden. Bitte melde dich beim Team.")
            self._sessions.pop(int(message.author.id), None)
            return
        next_q = questions[idx]
        try:
            await message.author.send(f"{idx + 1}/{len(questions)}: {next_q}")
        except Exception:
            pass


class _FakeInteraction:
    def __init__(self, guild: discord.Guild, user: discord.User):
        self.guild = guild
        self.user = user

    async def start_application(self, interaction: discord.Interaction, answers: list[str]):
        if not interaction.guild or not interaction.user:
            return False, "guild_only"

        cfg = self._config()
        enabled = bool(cfg.get("enabled", True))
        if not enabled:
            return False, "disabled"

        forum_id = int(cfg.get("forum_channel_id", 0) or 0)
        if not forum_id:
            return False, "forum_missing"

        guild = interaction.guild
        forum = guild.get_channel(forum_id)
        if not isinstance(forum, discord.ForumChannel):
            try:
                fetched = await self.bot.fetch_channel(int(forum_id))
                forum = fetched if isinstance(fetched, discord.ForumChannel) else None
            except Exception:
                forum = None
        if not isinstance(forum, discord.ForumChannel):
            return False, "forum_invalid"

        questions = self._questions()
        embed = build_application_embed(self.settings, guild, interaction.user, questions, answers)
        mention_role_id = int(cfg.get("ping_role_id", 0) or 0)
        mention = f"<@&{mention_role_id}>" if mention_role_id else ""
        title = f"📝 Bewerbung von {interaction.user.display_name}"

        created = await forum.create_thread(name=title[:100], content=mention or None, embeds=[embed])
        thread = created.thread

        app_id = await self.db.create_application(guild.id, interaction.user.id, thread.id, questions, answers)
        await self.logger.emit(
            self.bot,
            "application_created",
            {"application_id": int(app_id), "user_id": int(interaction.user.id), "thread_id": int(thread.id)},
        )
        return True, None

    async def send_dm_intro(self, user: discord.User, guild: discord.Guild | None):
        questions = self._questions()
        emb = build_application_dm_embed(self.settings, guild, questions)
        try:
            await user.send(embed=emb)
        except Exception:
            pass
        return questions
