from datetime import datetime
from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from database.session import Base

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    subjects = relationship("Subject", back_populates="course", cascade="all, delete-orphan")

class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    course = relationship("Course", back_populates="subjects")
    chapters = relationship("Chapter", back_populates="subject", cascade="all, delete-orphan")

class Chapter(Base):
    __tablename__ = "chapters"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    telegram_channel_id = Column(BigInteger, nullable=True)
    subject = relationship("Subject", back_populates="chapters")
    lectures = relationship("Lecture", back_populates="chapter", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="chapter", cascade="all, delete-orphan")

class Lecture(Base):
    __tablename__ = "lectures"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    telegram_message_id = Column(Integer, nullable=False, unique=True)
    file_name = Column(String(500))
    file_size = Column(BigInteger)
    duration = Column(Integer)
    mime_type = Column(String(100))
    width = Column(Integer)
    height = Column(Integer)
    supports_streaming = Column(Boolean, default=True)
    chapter = relationship("Chapter", back_populates="lectures")

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    telegram_message_id = Column(Integer, nullable=False, unique=True)
    file_name = Column(String(500))
    file_size = Column(BigInteger)
    mime_type = Column(String(100))
    chapter = relationship("Chapter", back_populates="documents")
