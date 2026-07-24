import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Chapter, Lecture, Document
from telegram.client import TelegramClient

logger = logging.getLogger(__name__)

class TelegramSyncService:
    def __init__(self, db: AsyncSession, tg: TelegramClient):
        self.db = db
        self.tg = tg

    async def sync_chapter(self, chapter_id: int):
        chapter = (await self.db.execute(select(Chapter).where(Chapter.id == chapter_id))).scalar_one_or_none()
        if not chapter or not chapter.telegram_channel_id:
            raise ValueError("Chapter not found or missing channel ID")
        messages = await self.tg.get_channel_messages(chapter.telegram_channel_id)
        vids = docs = 0
        for msg in messages:
            info = await self.tg.get_file_info(msg)
            if not info["file_name"]:
                continue
            if msg.video or (msg.document and "video" in (info["mime_type"] or "")):
                await self._upsert_lecture(chapter, msg, info)
                vids += 1
            elif msg.document and "pdf" in (info["mime_type"] or ""):
                await self._upsert_document(chapter, msg, info)
                docs += 1
        await self.db.commit()
        return {"videos": vids, "documents": docs}

    async def sync_all(self):
        chapters = (await self.db.execute(select(Chapter))).scalars().all()
        total = {"videos": 0, "documents": 0}
        for ch in chapters:
            if ch.telegram_channel_id:
                r = await self.sync_chapter(ch.id)
                total["videos"] += r["videos"]
                total["documents"] += r["documents"]
        return total

    async def _upsert_lecture(self, chapter, msg, info):
        existing = (await self.db.execute(select(Lecture).where(Lecture.telegram_message_id == msg.id))).scalar_one_or_none()
        if existing:
            existing.title = info["file_name"]
            existing.file_size = info["file_size"]
            existing.mime_type = info["mime_type"]
            existing.duration = info.get("duration")
            existing.width = info.get("width")
            existing.height = info.get("height")
        else:
            lec = Lecture(
                title=msg.caption or info["file_name"],
                chapter_id=chapter.id,
                telegram_message_id=msg.id,
                file_name=info["file_name"],
                file_size=info["file_size"],
                duration=info.get("duration"),
                mime_type=info["mime_type"],
                width=info.get("width"),
                height=info.get("height")
            )
            self.db.add(lec)

    async def _upsert_document(self, chapter, msg, info):
        existing = (await self.db.execute(select(Document).where(Document.telegram_message_id == msg.id))).scalar_one_or_none()
        if existing:
            existing.title = info["file_name"]
            existing.file_size = info["file_size"]
            existing.mime_type = info["mime_type"]
        else:
            doc = Document(
                title=msg.caption or info["file_name"],
                chapter_id=chapter.id,
                telegram_message_id=msg.id,
                file_name=info["file_name"],
                file_size=info["file_size"],
                mime_type=info["mime_type"]
            )
            self.db.add(doc)
