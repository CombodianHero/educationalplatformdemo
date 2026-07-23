"""
Auto Session Manager - Generates session string on first run
"""

import os
import asyncio
import logging
from pathlib import Path
from pyrogram import Client

logger = logging.getLogger(__name__)

class SessionManager:
    """Handles automatic session generation and management"""
    
    def __init__(self, api_id: int, api_hash: str):
        self.api_id = api_id
        self.api_hash = api_hash
        self.env_file = Path(__file__).parent.parent / ".env"
        
    async def get_or_create_session(self) -> str:
        """
        Get existing session or create new one interactively
        """
        # Check if session exists in .env
        session_string = os.getenv("SESSION_STRING", "")
        
        if session_string and session_string != "":
            if await self._validate_session(session_string):
                logger.info("✅ Valid session string found")
                return session_string
        
        # No valid session - create new one
        logger.info("🔑 No valid session found. Starting interactive login...")
        return await self._create_new_session()
    
    async def _validate_session(self, session_string: str) -> bool:
        """Check if session string is valid"""
        try:
            client = Client(
                "validate_temp",
                api_id=self.api_id,
                api_hash=self.api_hash,
                session_string=session_string,
                in_memory=True,
                no_updates=True
            )
            await client.start()
            me = await client.get_me()
            await client.stop()
            logger.info(f"Session valid - Logged in as {me.first_name}")
            return True
        except Exception as e:
            logger.warning(f"Invalid session: {e}")
            return False
    
    async def _create_new_session(self) -> str:
        """Interactive session creation"""
        print("\n" + "="*60)
        print("📱 TELEGRAM LOGIN REQUIRED")
        print("="*60)
        print("You need to login to create a session string.")
        print("This is a ONE-TIME process.\n")
        
        phone = input("📞 Enter phone number (with country code): +")
        
        client = Client(
            "new_session",
            api_id=self.api_id,
            api_hash=self.api_hash,
            in_memory=True
        )
        
        await client.start(phone=f"+{phone}")
        
        # Get verification code
        code = input("\n📨 Enter verification code from Telegram: ")
        
        try:
            await client.sign_in(f"+{phone}", code)
        except Exception as e:
            if "password" in str(e).lower():
                password = input("🔒 Enter 2FA password: ")
                await client.check_password(password)
        
        # Export session string
        session_string = await client.export_session_string()
        
        me = await client.get_me()
        print(f"\n✅ Logged in as {me.first_name} (@{me.username})")
        
        # Save to .env file
        await self._save_to_env(session_string)
        
        await client.stop()
        
        print("💾 Session saved to .env file")
        print("🚀 You won't need to login again!\n")
        
        return session_string
    
    async def _save_to_env(self, session_string: str):
        """Save session string to .env file"""
        if not self.env_file.exists():
            logger.error(".env file not found")
            return
        
        # Read existing .env
        with open(self.env_file, 'r') as f:
            lines = f.readlines()
        
        # Update or add SESSION_STRING
        session_found = False
        for i, line in enumerate(lines):
            if line.startswith("SESSION_STRING="):
                lines[i] = f'SESSION_STRING={session_string}\n'
                session_found = True
                break
        
        if not session_found:
            lines.append(f'\nSESSION_STRING={session_string}\n')
        
        # Write back
        with open(self.env_file, 'w') as f:
            f.writelines(lines)
        
        # Update current environment
        os.environ["SESSION_STRING"] = session_string
