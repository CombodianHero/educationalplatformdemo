"""
Course, Subject, Chapter API routes
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from database.session import get_db
from database.models import Course, Subject, Chapter, Lecture, Document
from utils.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for responses
class CourseResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    thumbnail_url: Optional[str]
    
    class Config:
        from_attributes = True


class SubjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    course_id: int
    
    class Config:
        from_attributes = True


class ChapterResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    subject_id: int
    
    class Config:
        from_attributes = True


class LectureResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    telegram_message_id: int
    file_name: Optional[str]
    file_size: Optional[int]
    duration: Optional[int]
    mime_type: Optional[str]
    thumbnail_url: Optional[str]
    
    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    telegram_message_id: int
    file_name: Optional[str]
    file_size: Optional[int]
    mime_type: Optional[str]
    
    class Config:
        from_attributes = True


@router.get("/courses", response_model=List[CourseResponse])
async def get_courses(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all courses
    
    Returns:
        List of courses
    """
    result = await db.execute(select(Course).order_by(Course.name))
    courses = result.scalars().all()
    return courses


@router.get("/course/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific course by ID
    
    Args:
        course_id: Course ID
        
    Returns:
        Course details
    """
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    return course


@router.get("/course/{course_id}/subjects", response_model=List[SubjectResponse])
async def get_course_subjects(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all subjects for a course
    
    Args:
        course_id: Course ID
        
    Returns:
        List of subjects
    """
    result = await db.execute(
        select(Subject)
        .where(Subject.course_id == course_id)
        .order_by(Subject.name)
    )
    subjects = result.scalars().all()
    return subjects


@router.get("/subject/{subject_id}/chapters", response_model=List[ChapterResponse])
async def get_subject_chapters(
    subject_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all chapters for a subject
    
    Args:
        subject_id: Subject ID
        
    Returns:
        List of chapters
    """
    result = await db.execute(
        select(Chapter)
        .where(Chapter.subject_id == subject_id)
        .order_by(Chapter.name)
    )
    chapters = result.scalars().all()
    return chapters


@router.get("/chapter/{chapter_id}/lectures", response_model=List[LectureResponse])
async def get_chapter_lectures(
    chapter_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all lectures for a chapter
    
    Args:
        chapter_id: Chapter ID
        
    Returns:
        List of lectures
    """
    result = await db.execute(
        select(Lecture)
        .where(Lecture.chapter_id == chapter_id)
        .order_by(Lecture.title)
    )
    lectures = result.scalars().all()
    return lectures


@router.get("/chapter/{chapter_id}/documents", response_model=List[DocumentResponse])
async def get_chapter_documents(
    chapter_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all documents for a chapter
    
    Args:
        chapter_id: Chapter ID
        
    Returns:
        List of documents
    """
    result = await db.execute(
        select(Document)
        .where(Document.chapter_id == chapter_id)
        .order_by(Document.title)
    )
    documents = result.scalars().all()
    return documents
