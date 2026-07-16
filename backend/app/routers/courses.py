import fitz  # PyMuPDF
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, CurrentUser
from app.core.database import get_db
from app.core.supabase_client import supabase
from app.core.config import settings
from app.core.llm import generate_course_structure
from app.models.models import Document, Course, Chapter, Lesson
from app.services.chunking import chunk_text
from app.services.embeddings import embed_texts
from app.services.vector_store import store_chunks

router = APIRouter(prefix="/courses", tags=["courses"])


def _get_owned_document(db: Session, document_id: str, user_id: str) -> Document:
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == user_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.post("/generate/{document_id}")
def generate_course(
    document_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = _get_owned_document(db, document_id, user.id)

    # 1. Re-download the PDF from storage and re-extract text.
    # (Day 1's upload endpoint doesn't persist full text — only metadata —
    # so we pull the original file back and extract again here.)
    try:
        file_bytes = supabase.storage.from_(settings.supabase_storage_bucket).download(document.storage_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not fetch stored PDF: {e}")

    pdf = fitz.open(stream=file_bytes, filetype="pdf")
    full_text = "\n\n".join(page.get_text() for page in pdf)
    pdf.close()

    if not full_text.strip():
        raise HTTPException(status_code=422, detail="No extractable text in this document")

    document.status = "generating"
    db.commit()

    # 2. Chunk + embed + store for RAG (chatbot in Day 4 will query these).
    chunks = chunk_text(full_text)
    embeddings = embed_texts(chunks)
    store_chunks(db, document.id, chunks, embeddings)

    # 3. Ask the LLM to structure the content into a course.
    try:
        structure = generate_course_structure(full_text)
    except Exception as e:
        document.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Course generation failed: {e}")

    # 4. Persist course -> chapters -> lessons.
    course = Course(
        document_id=document.id,
        user_id=user.id,
        title=structure.get("title", document.filename),
        description=structure.get("description"),
        estimated_time_minutes=structure.get("estimated_time_minutes"),
        difficulty_level=structure.get("difficulty_level"),
        learning_objectives=structure.get("learning_objectives", []),
        prerequisites=structure.get("prerequisites", []),
        status="ready",
    )
    db.add(course)
    db.flush()  # get course.id before inserting children

    for chapter_order, chapter_data in enumerate(structure.get("chapters", [])):
        chapter = Chapter(
            course_id=course.id,
            title=chapter_data.get("title", f"Chapter {chapter_order + 1}"),
            order=chapter_order,
            summary=chapter_data.get("summary"),
        )
        db.add(chapter)
        db.flush()

        for lesson_order, lesson_data in enumerate(chapter_data.get("lessons", [])):
            lesson = Lesson(
                chapter_id=chapter.id,
                title=lesson_data.get("title", f"Lesson {lesson_order + 1}"),
                order=lesson_order,
                content_markdown=lesson_data.get("content_markdown"),
                key_takeaways=lesson_data.get("key_takeaways", []),
                important_notes=lesson_data.get("important_notes", []),
                real_world_examples=lesson_data.get("real_world_examples", []),
                summary=lesson_data.get("summary"),
            )
            db.add(lesson)

    document.status = "ready"
    db.commit()
    db.refresh(course)

    return {"course_id": course.id, "title": course.title, "status": course.status}


@router.get("/")
def list_courses(
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    courses = db.query(Course).filter(Course.user_id == user.id).order_by(Course.created_at.desc()).all()
    return [
        {"id": c.id, "title": c.title, "status": c.status, "difficulty_level": c.difficulty_level}
        for c in courses
    ]


@router.get("/{course_id}")
def get_course(
    course_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "estimated_time_minutes": course.estimated_time_minutes,
        "difficulty_level": course.difficulty_level,
        "learning_objectives": course.learning_objectives,
        "prerequisites": course.prerequisites,
        "chapters": [
            {
                "id": ch.id,
                "title": ch.title,
                "order": ch.order,
                "summary": ch.summary,
                "lessons": [
                    {
                        "id": l.id,
                        "title": l.title,
                        "order": l.order,
                        "content_markdown": l.content_markdown,
                        "key_takeaways": l.key_takeaways,
                        "important_notes": l.important_notes,
                        "real_world_examples": l.real_world_examples,
                        "summary": l.summary,
                    }
                    for l in sorted(ch.lessons, key=lambda x: x.order)
                ],
            }
            for ch in sorted(course.chapters, key=lambda x: x.order)
        ],
    }
