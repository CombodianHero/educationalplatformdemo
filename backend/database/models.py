"""
SQLAlchemy database models for the streaming platform
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, BigInteger, DateTime, 
    ForeignKey, Text, Float, Boolean
)
from sqlalchemy.orm import relationship

from database.session import Base


class Course(Base):
    """Course model - top level organization"""
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subjects = relationship("Subject", back_populates="course", cascade="all, delete-orphan")


class Subject(Base):
    """Subject model - belongs to a course"""
    __tablename__ = "subjects"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    course = relationship("Course", back_populates="subjects")
    chapters = relationship("Chapter", back_populates="subject", cascade="all, delete-orphan")


class Chapter(Base):
    """Chapter model - belongs to a subject"""
    __tablename__ = "chapters"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    telegram_channel_id = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subject = relationship("Subject", back_populates="chapters")
    lectures = relationship("Lecture", back_populates="chapter", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="chapter", cascade="all, delete-orphan")


class Lecture(Base):
    """Lecture model - video content from Telegram"""
    __tablename__ = "lectures"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    telegram_message_id = Column(Integer, nullable=False, unique=True)
    file_name = Column(String(500), nullable=True)
    file_size = Column(BigInteger, nullable=True)  # Size in bytes
    duration = Column(Integer, nullable=True)  # Duration in seconds
    mime_type = Column(String(100), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    chapter = relationship("Chapter", back_populates="lectures")
    
    # Streaming metadata
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    supports_streaming = Column(Boolean, default=True)


class Document(Base):
    """Document model - PDF and other documents from Telegram"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    telegram_message_id = Column(Integer, nullable=False, unique=True)
    file_name = Column(String(500), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    mime_type = Column(String(100), nullable=True)
    page_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    chapter = relationship("Chapter", back_populates="documents")
