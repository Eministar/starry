import os
import json
import asyncio
import discord
from datetime import timedelta
from fastapi import FastAPI, Request, HTTPException, WebSocket
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from bot.modules.tickets.services.ticket_service import TicketService
from bot.modules.moderation.services.mod_service import ModerationService

class WebServer:
    def __init__(self, settings, db, bot):
        self.settings = settings
        self.db = db
        self.bot = bot
        self.ticket_service = TicketService(bot, settings, db, getattr(bot, "logger", None))
        self.moderation_service = ModerationService(bot, settings, db, getattr(bot, "forum_logs", None))
        self.app = FastAPI()
        self._server = None
        self._task = None

        base = os.path.dirname(__file__)
        static_dir = os.path.join(base, "static")

        self.app.mount("/static", StaticFiles(directory=static_dir), name="static")

        @self.app.get("/")
        async def index():
            return FileResponse(os.path.join(static_dir, "index.html"))

        @self.app.get("/api/settings")
        async def get_settings(request: Request):
            self._auth(request)
            return JSONResponse(self.settings.dump())

        @self.app.put("/api/settings")
        async def put_settings(request: Request):
            self._auth(request)
            data = await request.json()
            if not isinstance(data, dict):
                raise HTTPException(status_code=400, detail="Invalid settings payload")
            await self.settings.replace_overrides(data)
            return JSONResponse({"ok": True})

        @self.app.get("/api/tickets")
        async def list_tickets(request: Request, limit: int = 200):
            self._auth(request)
            rows = await self.db.list_tickets(limit=limit)
            out = []
            for r in rows:
                out.append({
                    "id": r[0],
                    "user_id": r[1],
                    "thread_id": r[2],
                    "status": r[3],
                    "claimed_by": r[4],
                    "created_at": r[5],
                    "closed_at": r[6],
                    "rating": r[7]
                })
            return JSONResponse(out)

        @self.app.get("/api/summary")
        async def summary(request: Request):
            self._auth(request)
            stats = await self.db.count_tickets_by_status()
            return JSONResponse(stats)

        @self.app.get("/api/logs")
        async def list_logs(request: Request, limit: int = 200):
            self._auth(request)
            rows = await self.db.list_logs(limit=limit)
            out = []
            for r in rows:
                out.append({
                    "id": r[0],
                    "event": r[1],
                    "payload": r[2],
                    "created_at": r[3],
                })
            return JSONResponse(out)

        @self.app.get("/api/snippets")
        async def get_snippets(request: Request):
            self._auth(request)
            data = self.settings.get("ticket.snippets", {}) or {}
            return JSONResponse(data)

        @self.app.put("/api/snippets")
        async def put_snippets(request: Request):
            self._auth(request)
            data = await request.json()
            if not isinstance(data, dict):
                raise HTTPException(status_code=400, detail="Invalid snippets payload")
            await self.settings.set_override("ticket.snippets", data)
            return JSONResponse({"ok": True})

        @self.app.get("/api/applications")
        async def get_applications(request: Request):
            self._auth(request)
            data = self.settings.get("applications", {}) or {}
            return JSONResponse(data)

        @self.app.put("/api/applications")
        async def put_applications(request: Request):
            self._auth(request)
            data = await request.json()
            if not isinstance(data, dict):
                raise HTTPException(status_code=400, detail="Invalid applications payload")
            await self.settings.set_override("applications", data)
            return JSONResponse({"ok": True})

        @self.app.get("/api/applications/list")
        async def list_applications(request: Request, limit: int = 200):
            self._auth(request)
            rows = await self.db.list_applications(limit=limit)
            out = []
            for r in rows:
                out.append({
                    "id": r[0],
                    "user_id": r[1],
                    "thread_id": r[2],
                    "status": r[3],
                    "created_at": r[4],
                    "closed_at": r[5],
                })
            return JSONResponse(out)

        @self.app.websocket("/ws/logs")
        async def ws_logs(websocket):
            token = websocket.query_params.get("token", "")
            if not token:
                await websocket.close(code=4401)
                return
            expected = self.settings.get("bot.dashboard.token", "change-me-now")
            if token != expected:
                await websocket.close(code=4403)
                return

            await websocket.accept()
            last_id = 0
            try:
                while True:
                    rows = await self.db.list_logs(limit=50)
                    rows = list(reversed(rows))
                    for r in rows:
                        if int(r[0]) <= last_id:
                            continue
                        payload = {"id": r[0], "event": r[1], "payload": r[2], "created_at": r[3]}
                        await websocket.send_json(payload)
                        last_id = int(r[0])
                    await asyncio.sleep(2.0)
            except Exception:
                try:
                    await websocket.close()
                except Exception:
                    pass

        @self.app.get("/api/users/search")
        async def search_users(request: Request, query: str):
            self._auth(request)
            guild = await self._guild()
            if not guild:
                raise HTTPException(status_code=404, detail="Guild not found")
            q = (query or "").lower()
            out = []
            for m in guild.members:
                if q in str(m.id) or q in m.name.lower() or q in m.display_name.lower():
                    out.append({"id": m.id, "name": m.name, "display_name": m.display_name})
                    if len(out) >= 25:
                        break
            return JSONResponse(out)

        @self.app.get("/api/users/live")
        async def live_users(request: Request, limit: int = 50):
            self._auth(request)
            guild = await self._guild()
            if not guild:
                raise HTTPException(status_code=404, detail="Guild not found")
            out = []
            for m in guild.members:
                if m.status in (discord.Status.online, discord.Status.idle, discord.Status.dnd):
                    out.append({
                        "id": m.id,
                        "name": m.name,
                        "display_name": m.display_name,
                        "status": str(m.status)
                    })
                if len(out) >= limit:
                    break
            return JSONResponse(out)

        @self.app.post("/api/discord/message")
        async def send_message(request: Request):
            self._auth(request)
            data = await request.json()
            channel_id = self._int(data.get("channel_id", 0))
            content = str(data.get("content", "")).strip()
            if not channel_id or not content:
                raise HTTPException(status_code=400, detail="Missing channel_id/content")
            ch = await self._channel(channel_id)
            if not ch:
                raise HTTPException(status_code=404, detail="Channel not found")
            await ch.send(content=content)
            return JSONResponse({"ok": True})

        @self.app.post("/api/discord/embed")
        async def send_embed(request: Request):
            self._auth(request)
            data = await request.json()
            channel_id = self._int(data.get("channel_id", 0))
            title = str(data.get("title", "")).strip()
            description = str(data.get("description", "")).strip()
            color = data.get("color", None)
            footer = str(data.get("footer", "")).strip()
            thumbnail = str(data.get("thumbnail", "")).strip()
            image = str(data.get("image", "")).strip()
            fields = data.get("fields", [])
            if not channel_id or not title:
                raise HTTPException(status_code=400, detail="Missing channel_id/title")
            ch = await self._channel(channel_id)
            if not ch:
                raise HTTPException(status_code=404, detail="Channel not found")
            c = None
            try:
                if color:
                    c = int(str(color).replace("#", ""), 16)
            except Exception:
                c = None
            emb = discord.Embed(title=title, description=description or None, color=c)
            if isinstance(fields, list):
                for f in fields[:25]:
                    try:
                        name = str(f.get("name", "")).strip()
                        value = str(f.get("value", "")).strip()
                        inline = bool(f.get("inline", False))
                        if name and value:
                            emb.add_field(name=name, value=value, inline=inline)
                    except Exception:
                        pass
            if footer:
                emb.set_footer(text=footer)
            if thumbnail:
                emb.set_thumbnail(url=thumbnail)
            if image:
                emb.set_image(url=image)
            await ch.send(embed=emb)
            return JSONResponse({"ok": True})

        @self.app.post("/api/moderation/timeout")
        async def mod_timeout(request: Request):
            self._auth(request)
            data = await request.json()
            user_id = self._int(data.get("user_id", 0))
            minutes = self._int(data.get("minutes", 0))
            moderator_id = self._int(data.get("moderator_id", 0))
            reason = str(data.get("reason", "")).strip() or None
            guild = await self._guild()
            if not guild or not user_id:
                raise HTTPException(status_code=404, detail="Guild/User not found")
            member = guild.get_member(user_id)
            if not member:
                raise HTTPException(status_code=404, detail="Member not found")
            moderator = guild.get_member(moderator_id) if moderator_id else None
            if moderator:
                await self.moderation_service.timeout(guild, moderator, member, minutes, reason)
            else:
                until = discord.utils.utcnow() + timedelta(minutes=minutes)
                if hasattr(member, "timeout"):
                    await member.timeout(until, reason=reason)
                else:
                    await member.edit(timed_out_until=until, reason=reason)
            return JSONResponse({"ok": True})

        @self.app.post("/api/moderation/kick")
        async def mod_kick(request: Request):
            self._auth(request)
            data = await request.json()
            user_id = self._int(data.get("user_id", 0))
            moderator_id = self._int(data.get("moderator_id", 0))
            reason = str(data.get("reason", "")).strip() or None
            guild = await self._guild()
            member = guild.get_member(user_id) if guild else None
            if not member:
                raise HTTPException(status_code=404, detail="Member not found")
            moderator = guild.get_member(moderator_id) if moderator_id and guild else None
            if moderator:
                await self.moderation_service.kick(guild, moderator, member, reason)
            else:
                await member.kick(reason=reason)
            return JSONResponse({"ok": True})

        @self.app.post("/api/moderation/ban")
        async def mod_ban(request: Request):
            self._auth(request)
            data = await request.json()
            user_id = self._int(data.get("user_id", 0))
            delete_days = self._int(data.get("delete_days", 0))
            moderator_id = self._int(data.get("moderator_id", 0))
            reason = str(data.get("reason", "")).strip() or None
            guild = await self._guild()
            if not guild or not user_id:
                raise HTTPException(status_code=404, detail="Guild/User not found")
            user = await self.bot.fetch_user(user_id)
            moderator = guild.get_member(moderator_id) if moderator_id else None
            if moderator:
                await self.moderation_service.ban(guild, moderator, user, delete_days, reason)
            else:
                await guild.ban(user, reason=reason, delete_message_days=max(0, min(7, delete_days)))
            return JSONResponse({"ok": True})

        @self.app.post("/api/moderation/purge")
        async def mod_purge(request: Request):
            self._auth(request)
            data = await request.json()
            channel_id = self._int(data.get("channel_id", 0))
            amount = self._int(data.get("amount", 0))
            user_id = self._int(data.get("user_id", 0) or 0)
            moderator_id = self._int(data.get("moderator_id", 0))
            ch = await self._channel(channel_id)
            if not isinstance(ch, discord.TextChannel):
                raise HTTPException(status_code=404, detail="Channel not found")
            guild = await self._guild()
            moderator = guild.get_member(moderator_id) if guild and moderator_id else None
            if moderator:
                deleted, _err = await self.moderation_service.purge(guild, moderator, ch, amount, guild.get_member(user_id) if user_id else None)
                return JSONResponse({"ok": True, "deleted": int(deleted)})
            else:
                def check(m: discord.Message):
                    return m.author.id == user_id if user_id else True
                deleted = await ch.purge(limit=max(1, min(100, amount)), check=check, bulk=True)
                return JSONResponse({"ok": True, "deleted": len(deleted)})

        @self.app.post("/api/roles/add")
        async def roles_add(request: Request):
            self._auth(request)
            data = await request.json()
            user_id = self._int(data.get("user_id", 0))
            role_id = self._int(data.get("role_id", 0))
            guild = await self._guild()
            if not guild:
                raise HTTPException(status_code=404, detail="Guild not found")
            member = guild.get_member(user_id)
            role = guild.get_role(role_id)
            if not member or not role:
                raise HTTPException(status_code=404, detail="Member/Role not found")
            await member.add_roles(role, reason="Dashboard")
            return JSONResponse({"ok": True})

        @self.app.post("/api/roles/remove")
        async def roles_remove(request: Request):
            self._auth(request)
            data = await request.json()
            user_id = self._int(data.get("user_id", 0))
            role_id = self._int(data.get("role_id", 0))
            guild = await self._guild()
            if not guild:
                raise HTTPException(status_code=404, detail="Guild not found")
            member = guild.get_member(user_id)
            role = guild.get_role(role_id)
            if not member or not role:
                raise HTTPException(status_code=404, detail="Member/Role not found")
            await member.remove_roles(role, reason="Dashboard")
            return JSONResponse({"ok": True})

        @self.app.post("/api/tickets/action")
        async def ticket_action(request: Request):
            self._auth(request)
            data = await request.json()
            thread_id = self._int(data.get("thread_id", 0))
            action = str(data.get("action", "")).strip()
            user_id = self._int(data.get("user_id", 0) or 0)
            actor_id = self._int(data.get("actor_id", 0) or 0)
            guild = await self._guild()
            if not guild:
                raise HTTPException(status_code=404, detail="Guild not found")
            thread = guild.get_thread(thread_id)
            if not thread:
                fetched = await self.bot.fetch_channel(thread_id)
                thread = fetched if isinstance(fetched, discord.Thread) else None
            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")
            actor = guild.get_member(actor_id) if actor_id else None
            if not actor:
                raise HTTPException(status_code=404, detail="Actor not found")

            if action == "close":
                ok, err = await self.ticket_service.dashboard_close_ticket(guild, thread, actor, reason=data.get("reason"))
            elif action == "claim":
                ok, err = await self.ticket_service.dashboard_set_claim(guild, thread, actor, claimed=True)
            elif action == "release":
                ok, err = await self.ticket_service.dashboard_set_claim(guild, thread, actor, claimed=False)
            elif action == "add_user":
                if not user_id:
                    raise HTTPException(status_code=400, detail="Missing user_id")
                user = await self.bot.fetch_user(user_id)
                ok, err = await self.ticket_service.dashboard_add_participant(guild, thread, actor, user)
            else:
                raise HTTPException(status_code=400, detail="Invalid action")

            if not ok:
                raise HTTPException(status_code=400, detail=err or "Ticket action failed")
            return JSONResponse({"ok": True})
        @self.app.get("/api/summary")
        async def summary(request: Request):
            self._auth(request)
            stats = await self.db.count_tickets_by_status()
            return JSONResponse(stats)

    def _auth(self, request: Request):
        token = self.settings.get("bot.dashboard.token", "change-me-now")
        header = request.headers.get("authorization", "")
        if not header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing token")
        if header.split("Bearer ", 1)[1].strip() != token:
            raise HTTPException(status_code=403, detail="Invalid token")

    def _int(self, value) -> int:
        try:
            return int(value)
        except Exception:
            return 0

    async def _guild(self) -> discord.Guild | None:
        gid = self.settings.get_int("bot.guild_id")
        if not gid:
            return None
        g = self.bot.get_guild(int(gid))
        if g:
            return g
        try:
            return await self.bot.fetch_guild(int(gid))
        except Exception:
            return None

    async def _channel(self, channel_id: int):
        ch = self.bot.get_channel(int(channel_id))
        if ch:
            return ch
        try:
            return await self.bot.fetch_channel(int(channel_id))
        except Exception:
            return None

    async def start(self):
        host = self.settings.get("bot.dashboard.host", "0.0.0.0")
        port = int(self.settings.get("bot.dashboard.port", 8787))
        config = uvicorn.Config(self.app, host=host, port=port, log_level="warning")
        self._server = uvicorn.Server(config)
        loop = asyncio.get_running_loop()
        self._task = loop.create_task(self._server.serve())
