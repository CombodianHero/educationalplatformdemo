"""
Admin API routes for managing content and syncing Telegram
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from database.session import get_db
from database.models import Course, Subject, Chapter
from utils.security import get_admin_user
from telegram.client import TelegramClient
from services.sync_service import TelegramSyncService

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for requests
class CourseCreate(BaseModel):
    name: str
    description: Optional[str] = None


class SubjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    course_id: int


class ChapterCreate(BaseModel):
    name: str
    description: Optional[str] = None
    subject_id: int
    telegram_channel_id: int


@router.post("/admin/courses")
async def create_course(
    course_data: CourseCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    """
    Create a new course (Admin only)
    
    Args:
        course_data: Course name and description
        db: Database session
        admin_user: Admin user (injected)
        
    Returns:
        Created course
    """
    # Check if course already exists
    result = await db.execute(select(Course).where(Course.name == course_data.name))
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course with this name already exists"
        )
    
    course = Course(
        name=course_data.name,
        description=course_data.description
    )
    
    db.add(course)
    await db.commit()
    await db.refresh(course)
    
    logger.info(f"Course created: {course.name} by admin {admin_user['username']}")
    return course


@router.post("/admin/subjects")
async def create_subject(
    subject_data: SubjectCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    """
    Create a new subject (Admin only)
    
    Args:
        subject_data: Subject details
        db: Database session
        admin_user: Admin user (injected)
        
    Returns:
        Created subject
    """
    # Verify course exists
    result = await db.execute(select(Course).where(Course.id == subject_data.course_id))
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    subject = Subject(
        name=subject_data.name,
        description=subject_data.description,
        course_id=subject_data.course_id
    )
    
    db.add(subject)
    await db.commit()
    await db.refresh(subject)
    
    logger.info(f"Subject created: {subject.name} for course {course.name}")
    return subject


@router.post("/admin/chapters")
async def create_chapter(
    chapter_data: ChapterCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    """
    Create a new chapter (Admin only)
    
    Args:
        chapter_data: Chapter details including Telegram channel ID
        db: Database session
        admin_user: Admin user (injected)
        
    Returns:
        Created chapter
    """
    # Verify subject exists
    result = await db.execute(select(Subject).where(Subject.id == chapter_data.subject_id))
    subject = result.scalar_one_or_none()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    chapter = Chapter(
        name=chapter_data.name,
        description=chapter_data.description,
        subject_id=chapter_data.subject_id,
        telegram_channel_id=chapter_data.telegram_channel_id
    )
    
    db.add(chapter)
    await db.commit()
    await db.refresh(chapter)
    
    logger.info(f"Chapter created: {chapter.name} for subject {subject.name}")
    return chapter


@router.post("/telegram/sync")
async def sync_telegram_channel(
    chapter_id: Optional[int] = None,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    """
    Sync content from Telegram channel to database (Admin only)
    
    This scans the Telegram channel for videos and PDFs,
    and stores their metadata in the database.
    
    Args:
        chapter_id: Optional specific chapter to sync, or sync all
        request: FastAPI request object
        db: Database session
        admin_user: Admin user (injected)
        
    Returns:
        Sync results
    """
    telegram_client = request.app.state.telegram_client
    sync_service = TelegramSyncService(db, telegram_client)
    
    try:
        if chapter_id:
            # Sync specific chapter
            result = await sync_service.sync_chapter(chapter_id)
        else:
            # Sync all chapters
            result = await sync_service.sync_all_chapters()
        
        logger.info(f"Sync completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )
