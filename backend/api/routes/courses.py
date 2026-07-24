from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.session import get_db
from database.models import Course, Subject, Chapter, Lecture, Document
from utils.security import get_current_user

router = APIRouter()

@router.get("/courses")
async def get_courses(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return (await db.execute(select(Course))).scalars().all()

@router.get("/course/{course_id}/subjects")
async def get_subjects(course_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return (await db.execute(select(Subject).where(Subject.course_id == course_id))).scalars().all()

@router.get("/subject/{subject_id}/chapters")
async def get_chapters(subject_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return (await db.execute(select(Chapter).where(Chapter.subject_id == subject_id))).scalars().all()

@router.get("/chapter/{chapter_id}/lectures")
async def get_lectures(chapter_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return (await db.execute(select(Lecture).where(Lecture.chapter_id == chapter_id))).scalars().all()

@router.get("/chapter/{chapter_id}/documents")
async def get_documents(chapter_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return (await db.execute(select(Document).where(Document.chapter_id == chapter_id))).scalars().all()
