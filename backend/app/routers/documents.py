import uuid

import fitz  # PyMuPDF
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, CurrentUser
from app.core.database import get_db
from app.core.supabase_client import supabase
from app.core.config import settings
from app.models.models import Document

router = APIRouter(prefix="/documents", tags=["documents"])

MAX_FILE_SIZE_MB = 50


def extract_text_from_pdf(file_bytes: bytes) -> tuple[str, int]:
    """Extract all text from a PDF, page by page. Returns (full_text, page_count)."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages_text = []
    for page in doc:
        pages_text.append(page.get_text())
    page_count = doc.page_count
    doc.close()
    return "\n\n".join(pages_text), page_count


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_bytes = await file.read()
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=400, detail=f"File exceeds {MAX_FILE_SIZE_MB}MB limit")

    # 1. Extract text (do this before upload so we fail fast on corrupt PDFs)
    try:
        full_text, page_count = extract_text_from_pdf(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read PDF: {e}")

    if not full_text.strip():
        raise HTTPException(
            status_code=422,
            detail="No extractable text found. Scanned/image-only PDFs need OCR (not yet supported).",
        )

    # 2. Upload original file to Supabase Storage
    storage_path = f"{user.id}/{uuid.uuid4()}_{file.filename}"
    supabase.storage.from_(settings.supabase_storage_bucket).upload(
        storage_path,
        file_bytes,
        file_options={"content-type": "application/pdf"},
    )

    # 3. Save document metadata
    document = Document(
        user_id=user.id,
        filename=file.filename,
        storage_path=storage_path,
        page_count=page_count,
        char_count=len(full_text),
        status="extracted",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # NOTE: full_text is intentionally not stored on the Document row (keep table light).
    # Day 2 will chunk + store this text (and embeddings) in document_chunks for RAG,
    # and kick off course generation from it.

    return {
        "document_id": document.id,
        "filename": document.filename,
        "page_count": document.page_count,
        "char_count": document.char_count,
        "status": document.status,
        "preview": full_text[:500],
    }


@router.get("/")
def list_documents(
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    docs = db.query(Document).filter(Document.user_id == user.id).order_by(Document.created_at.desc()).all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "page_count": d.page_count,
            "status": d.status,
            "created_at": d.created_at,
        }
        for d in docs
    ]
