import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


def new_uuid():
    return str(uuid.uuid4())


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    user_id = Column(UUID(as_uuid=False), nullable=False)
    filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    page_count = Column(Integer)
    char_count = Column(Integer)
    status = Column(String, default="uploaded")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    courses = relationship("Course", back_populates="document", cascade="all, delete")


class Course(Base):
    __tablename__ = "courses"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    document_id = Column(UUID(as_uuid=False), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=False), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    estimated_time_minutes = Column(Integer)
    difficulty_level = Column(String)
    learning_objectives = Column(JSON)
    prerequisites = Column(JSON)
    status = Column(String, default="draft")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    document = relationship("Document", back_populates="courses")
    chapters = relationship("Chapter", back_populates="course", cascade="all, delete")


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    course_id = Column(UUID(as_uuid=False), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    order = Column("order", Integer, nullable=False)
    summary = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    course = relationship("Course", back_populates="chapters")
    lessons = relationship("Lesson", back_populates="chapter", cascade="all, delete")


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    chapter_id = Column(UUID(as_uuid=False), ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    order = Column("order", Integer, nullable=False)
    content_markdown = Column(Text)
    key_takeaways = Column(JSON)
    important_notes = Column(JSON)
    real_world_examples = Column(JSON)
    summary = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    chapter = relationship("Chapter", back_populates="lessons")


class LessonProgress(Base):
    __tablename__ = "lesson_progress"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    user_id = Column(UUID(as_uuid=False), nullable=False)
    lesson_id = Column(UUID(as_uuid=False), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True))
    time_spent_seconds = Column(Integer, default=0)
