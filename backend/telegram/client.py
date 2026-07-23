"""
Telegram MTProto client using Pyrogram
Handles connection, authentication, and file operations
"""

import logging
from typing import Optional, AsyncGenerator, BinaryIO
import io

from pyrogram import Client
from pyrogram.errors import FloodWait, RPCError
from pyrogram.types import Message
import asyncio

from utils.config import settings

logger = logging.getLogger(__name__)


class TelegramClient:
    """
    Wrapper around Pyrogram client for MTProto operations
    
    Handles:
    - Authentication via session string
    - Channel message retrieval
    - File downloading and streaming
    - Connection management
    """
    
    def __init__(self):
        """Initialize Telegram client with credentials"""
        self.client: Optional[Client] = None
        self._is_connected = False
        
        logger.info("Initializing Telegram MTProto client")
        
    async def start(self):
        """Start the Telegram client and authenticate"""
        try:
            self.client = Client(
                name="streaming_bot",
                api_id=settings.api_id,
                api_hash=settings.api_hash,
                session_string=settings.session_string,
                in_memory=True,  # Don't save session to disk
                no_updates=True  # We don't need updates for streaming
            )
            
            await self.client.start()
            self._is_connected = True
            
            # Verify connection
            me = await self.client.get_me()
            logger.info(f"Connected to Telegram as {me.first_name} (@{me.username})")
            
        except Exception as e:
            logger.error(f"Failed to start Telegram client: {e}")
            raise
    
    async def stop(self):
        """Stop the Telegram client"""
        if self.client:
            await self.client.stop()
            self._is_connected = False
            logger.info("Telegram client stopped")
    
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self._is_connected and self.client is not None
    
    async def get_channel_messages(
        self,
        channel_id: int,
        limit: int = 100,
        offset_id: int = 0
    ) -> list[Message]:
        """
        Retrieve messages from a Telegram channel
        
        Args:
            channel_id: Channel ID (negative for supergroups/channels)
            limit: Maximum number of messages to retrieve
            offset_id: Message ID to start from (for pagination)
            
        Returns:
            List of Pyrogram Message objects
        """
        if not self.is_connected():
            raise ConnectionError("Telegram client is not connected")
        
        try:
            messages = []
            async for message in self.client.get_chat_history(
                chat_id=channel_id,
                limit=limit,
                offset_id=offset_id
            ):
                messages.append(message)
            
            logger.info(f"Retrieved {len(messages)} messages from channel {channel_id}")
            return messages
            
        except FloodWait as e:
            logger.warning(f"Flood wait: {e.value} seconds")
            await asyncio.sleep(e.value)
            return await self.get_channel_messages(channel_id, limit, offset_id)
        except RPCError as e:
            logger.error(f"Telegram RPC error: {e}")
            raise
    
    async def get_file_size(self, message: Message) -> int:
        """
        Get file size from a message
        
        Args:
            message: Pyrogram Message object
            
        Returns:
            File size in bytes
        """
        if message.video:
            return message.video.file_size
        elif message.document:
            return message.document.file_size
        elif message.audio:
            return message.audio.file_size
        return 0
    
    async def stream_file(
        self,
        message: Message,
        offset: int = 0,
        chunk_size: int = 1024 * 1024
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream a file from Telegram in chunks
        
        Supports HTTP Range requests for video seeking
        
        Args:
            message: Pyrogram Message containing the file
            offset: Byte offset to start streaming from
            chunk_size: Size of each chunk in bytes
            
        Yields:
            Bytes chunks of the file
        """
        if not self.is_connected():
            raise ConnectionError("Telegram client is not connected")
        
        try:
            # Download file in chunks
            async for chunk in self.client.stream_media(
                message=message,
                offset=offset,
                limit=chunk_size,
            ):
                yield chunk
                
        except FloodWait as e:
            logger.warning(f"Flood wait during streaming: {e.value} seconds")
            await asyncio.sleep(e.value)
            async for chunk in self.stream_file(message, offset, chunk_size):
                yield chunk
        except Exception as e:
            logger.error(f"Error streaming file: {e}")
            raise
    
    async def get_file_info(self, message: Message) -> dict:
        """
        Extract file information from a message
        
        Args:
            message: Pyrogram Message object
            
        Returns:
            Dictionary with file metadata
        """
        file_info = {
            "message_id": message.id,
            "file_name": None,
            "file_size": 0,
            "mime_type": None,
            "duration": None,
            "thumbnail": None,
            "width": None,
            "height": None,
        }
        
        if message.video:
            file_info.update({
                "file_name": message.video.file_name or f"video_{message.id}.mp4",
                "file_size": message.video.file_size,
                "mime_type": message.video.mime_type,
                "duration": message.video.duration,
                "width": message.video.width,
                "height": message.video.height,
            })
            if message.video.thumbs:
                file_info["thumbnail"] = message.video.thumbs[0].file_id
        
        elif message.document:
            file_info.update({
                "file_name": message.document.file_name or f"document_{message.id}",
                "file_size": message.document.file_size,
                "mime_type": message.document.mime_type,
            })
            if message.document.thumbs:
                file_info["thumbnail"] = message.document.thumbs[0].file_id
        
        return file_info
