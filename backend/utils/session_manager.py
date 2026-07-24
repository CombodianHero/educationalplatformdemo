"""
Auto-generate Pyrogram session string on first run, save to .env
"""
import os
import asyncio
import logging
from pathlib import Path
from pyrogram import Client

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self, api_id: int, api_hash: str):
        self.api_id = api_id
        self.api_hash = api_hash
        self.env_path = Path(__file__).parent.parent / ".env"

    async def get_or_create_session(self) -> str:
        # Check existing
        existing = os.getenv("SESSION_STRING", "")
        if existing and await self._validate(existing):
            logger.info("✅ Valid session found in environment")
            return existing

        logger.info("🔑 No valid session. Starting interactive login...")
        return await self._interactive_login()

    async def _validate(self, session_str: str) -> bool:
        try:
            client = Client(":memory:", api_id=self.api_id, api_hash=self.api_hash,
                            session_string=session_str, no_updates=True)
            await client.start()
            me = await client.get_me()
            await client.stop()
            logger.info(f"Session valid (user: {me.first_name})")
            return True
        except Exception as e:
            logger.warning(f"Session invalid: {e}")
            return False

    async def _interactive_login(self) -> str:
        print("\n📱 Telegram Login required (one-time)")
        phone = input("Phone number (with country code): +")
        client = Client(":memory:", api_id=self.api_id, api_hash=self.api_hash)
        await client.start(phone=f"+{phone}")
        code = input("Verification code: ")
        try:
            await client.sign_in(f"+{phone}", code)
        except Exception as e:
            if "password" in str(e).lower():
                password = input("2FA password: ")
                await client.check_password(password)
        session_str = await client.export_session_string()
        me = await client.get_me()
        print(f"✅ Logged in as {me.first_name}")
        await client.stop()
        self._save_to_env(session_str)
        return session_str

    def _save_to_env(self, session_str: str):
        if not self.env_path.exists():
            return
        lines = self.env_path.read_text().splitlines()
        new_lines = []
        found = False
        for line in lines:
            if line.startswith("SESSION_STRING="):
                new_lines.append(f"SESSION_STRING={session_str}")
                found = True
            else:
                new_lines.append(line)
        if not found:
            new_lines.append(f"SESSION_STRING={session_str}")
        self.env_path.write_text("\n".join(new_lines) + "\n")
        os.environ["SESSION_STRING"] = session_str
