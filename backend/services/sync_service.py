"""
Service for syncing Telegram channel content to database
"""

import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import Chapter, Lecture, Document
from telegram.client import TelegramClient

logger = logging.getLogger(__name__)


class TelegramSyncService:
    """
    Synchronizes content from Telegram channels to the database
    
    Handles:
    - Scanning channels for videos and documents
    - Extracting metadata
    - Storing/updating records in database
    """
    
    def __init__(self, db: AsyncSession, telegram_client: TelegramClient):
        self.db = db
        self.telegram_client = telegram_client
    
    async def sync_chapter(self, chapter_id: int) -> Dict[str, Any]:
        """
        Sync content for a specific chapter
        
        Args:
            chapter_id: Chapter ID to sync
            
        Returns:
            Sync statistics
        """
        # Get chapter
        result = await self.db.execute(
            select(Chapter).where(Chapter.id == chapter_id)
        )
        chapter = result.scalar_one_or_none()
        
        if not chapter:
            raise ValueError(f"Chapter {chapter_id} not found")
        
        if not chapter.telegram_channel_id:
            raise ValueError(f"Chapter {chapter_id} has no Telegram channel ID")
        
        logger.info(f"Syncing chapter: {chapter.name} (ID: {chapter_id})")
        
        # Get messages from Telegram channel
        messages = await self.telegram_client.get_channel_messages(
            channel_id=chapter.telegram_channel_id,
            limit=100  # Adjust based on needs
        )
        
        videos_synced = 0
        documents_synced = 0
        skipped = 0
        
        for message in messages:
            file_info = await self.telegram_client.get_file_info(message)
            
            if not file_info["file_name"]:
                skipped += 1
                continue
            
            if message.video or (message.document and "video" in file_info.get("mime_type", "")):
                # It's a video
                await self._sync_video(chapter, message, file_info)
                videos_synced += 1
                
            elif message.document and "pdf" in file_info.get("mime_type", ""):
                # It's a PDF
                await self._sync_document(chapter, message, file_info)
                documents_synced += 1
                
            else:
                skipped += 1
        
        await self.db.commit()
        
        result = {
            "chapter_id": chapter_id,
            "chapter_name": chapter.name,
            "videos_synced": videos_synced,
            "documents_synced": documents_synced,
            "skipped": skipped,
            "total_messages": len(messages)
        }
        
        logger.info(f"Sync completed for chapter {chapter.name}: {result}")
        return result
    
    async def sync_all_chapters(self) -> Dict[str, Any]:
        """
        Sync all chapters in the database
        
        Returns:
            Combined sync statistics
        """
        result = await self.db.execute(select(Chapter))
        chapters = result.scalars().all()
        
        total_results = {
            "chapters_synced": 0,
            "total_videos": 0,
            "total_documents": 0,
            "total_skipped": 0,
            "details": []
        }
        
        for chapter in chapters:
            if chapter.telegram_channel_id:
                try:
                    chapter_result = await self.sync_chapter(chapter.id)
                    total_results["details"].append(chapter_result)
                    total_results["chapters_synced"] += 1
                    total_results["total_videos"] += chapter_result["videos_synced"]
                    total_results["total_documents"] += chapter_result["documents_synced"]
                    total_results["total_skipped"] += chapter_result["skipped"]
                except Exception as e:
                    logger.error(f"Failed to sync chapter {chapter.id}: {e}")
        
        return total_results
    
    async def _sync_video(self, chapter: Chapter, message, file_info: dict):
        """
        Sync a video message to the database
        
        Args:
            chapter: Chapter object
            message: Telegram message
            file_info: Extracted file information
        """
        # Check if video already exists
        result = await self.db.execute(
            select(Lecture).where(Lecture.telegram_message_id == message.id)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing record
            existing.title = file_info["file_name"]
            existing.file_size = file_info["file_size"]
            existing.mime_type = file_info["mime_type"]
            existing.duration = file_info["duration"]
            existing.file_name = file_info["file_name"]
            
            if file_info["width"]:
                existing.width = file_info["width"]
            if file_info["height"]:
                existing.height = file_info["height"]
            
            logger.debug(f"Updated video: {file_info['file_name']}")
        else:
            # Create new record
            lecture = Lecture(
                title=message.caption or file_info["file_name"],
                description=message.caption,
                chapter_id=chapter.id,
                telegram_message_id=message.id,
                file_name=file_info["file_name"],
                file_size=file_info["file_size"],
                duration=file_info["duration"],
                mime_type=file_info["mime_type"],
                width=file_info.get("width"),
                height=file_info.get("height"),
                supports_streaming=True
            )
            
            self.db.add(lecture)
            logger.debug(f"Added new video: {file_info['file_name']}")
    
    async def _sync_document(self, chapter: Chapter, message, file_info: dict):
        """
        Sync a document message to the database
        
        Args:
            chapter: Chapter object
            message: Telegram message
            file_info: Extracted file information
        """
        # Check if document already exists
        result = await self.db.execute(
            select(Document).where(Document.telegram_message_id == message.id)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing record
            existing.title = file_info["file_name"]
            existing.file_size = file_info["file_size"]
            existing.mime_type = file_info["mime_type"]
            existing.file_name = file_info["file_name"]
            
            logger.debug(f"Updated document: {file_info['file_name']}")
        else:
            # Create new record
            document = Document(
                title=message.caption or file_info["file_name"],
                description=message.caption,
                chapter_id=chapter.id,
                telegram_message_id=message.id,
                file_name=file_info["file_name"],
                file_size=file_info["file_size"],
                mime_type=file_info["mime_type"]
            )
            
            self.db.add(document)
            logger.debug(f"Added new document: {file_info['file_name']}")
