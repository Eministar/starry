from __future__ import annotations

import re
import httpx
import discord


_MENTION_RE = re.compile(r"<@!?\d+>")
_MAX_REPLY_CHARS = 500
_CHEAPEST_MODEL = "deepseek-chat"


class DeepSeekService:
    def __init__(self, bot: discord.Client, settings, logger):
        self.bot = bot
        self.settings = settings
        self.logger = logger

    def _g(self, guild_id: int, key: str, default=None):
        return self.settings.get_guild(guild_id, key, default)

    def _api_key(self, guild_id: int) -> str:
        return str(self._g(guild_id, "ai.deepseek_api_key", "") or "").strip()

    def _system_prompt(self, guild_id: int) -> str:
        return str(self._g(guild_id, "ai.system_prompt", "") or "").strip()

    def _model(self, guild_id: int) -> str:
        return _CHEAPEST_MODEL

    def _endpoint(self, guild_id: int) -> str:
        return str(self._g(guild_id, "ai.endpoint", "https://api.deepseek.com/chat/completions") or "").strip()

    async def generate_reply(self, guild_id: int, prompt: str) -> tuple[str | None, str | None]:
        api_key = self._api_key(guild_id)
        if not api_key:
            return None, "API-Key fehlt"

        system_prompt = self._system_prompt(guild_id)
        model = self._model(guild_id)
        endpoint = self._endpoint(guild_id)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.8,
            "max_tokens": 220,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(endpoint, json=payload, headers=headers)
                if resp.status_code >= 400:
                    return None, f"HTTP {resp.status_code}"
                data = resp.json()
        except Exception:
            return None, "Request fehlgeschlagen"

        try:
            choices = data.get("choices") or []
            content = choices[0]["message"]["content"]
            reply = str(content).strip()
            if len(reply) > _MAX_REPLY_CHARS:
                reply = reply[: _MAX_REPLY_CHARS].rstrip()
            return reply, None
        except Exception:
            return None, "Antwort ungueltig"

    def clean_prompt(self, bot_user_id: int, text: str) -> str:
        if not text:
            return ""
        text = _MENTION_RE.sub("", text)
        return text.strip()
