from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.models import models  # noqa: ensures models are registered before create_all
from app.routers import documents, courses

app = FastAPI(title="PDF to E-Course Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(courses.router)


@app.on_event("startup")
def on_startup():
    # Day 1: auto-create tables for local dev convenience.
    # In production, prefer running schema.sql manually via Supabase SQL editor.
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}
