import logging
from typing import AsyncGenerator
from pyrogram import Client
from pyrogram.errors import FloodWait, RPCError
from pyrogram.types import Message
import asyncio
from utils.config import settings

logger = logging.getLogger(__name__)

class TelegramClient:
    def __init__(self):
        self.client: Client = None
        self._connected = False

    async def start(self):
        self.client = Client(
            name="edu_stream",
            api_id=settings.api_id,
            api_hash=settings.api_hash,
            session_string=settings.session_string,
            in_memory=True,
            no_updates=True
        )
        await self.client.start()
        self._connected = True
        me = await self.client.get_me()
        logger.info(f"Telegram connected as {me.first_name}")

    async def stop(self):
        if self.client:
            await self.client.stop()
            self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    async def get_channel_messages(self, channel_id: int, limit: int = 100) -> list[Message]:
        messages = []
        async for msg in self.client.get_chat_history(chat_id=channel_id, limit=limit):
            messages.append(msg)
        return messages

    async def stream_file(self, message: Message, offset: int = 0, chunk_size: int = 1024*1024) -> AsyncGenerator[bytes, None]:
        try:
            async for chunk in self.client.stream_media(message, offset=offset, limit=chunk_size):
                yield chunk
        except FloodWait as e:
            logger.warning(f"Flood wait {e.value}s")
            await asyncio.sleep(e.value)
            async for chunk in self.stream_file(message, offset, chunk_size):
                yield chunk

    async def get_file_info(self, message: Message) -> dict:
        info = {"message_id": message.id, "file_name": None, "file_size": 0, "mime_type": None}
        if message.video:
            info.update({
                "file_name": message.video.file_name or f"video_{message.id}.mp4",
                "file_size": message.video.file_size,
                "mime_type": message.video.mime_type,
                "duration": message.video.duration,
                "width": message.video.width,
                "height": message.video.height
            })
        elif message.document:
            info.update({
                "file_name": message.document.file_name,
                "file_size": message.document.file_size,
                "mime_type": message.document.mime_type
            })
        return info
