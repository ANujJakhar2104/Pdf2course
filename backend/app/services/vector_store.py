"""
Stores and retrieves document chunk embeddings in the `document_chunks`
table (pgvector). We use raw SQL here rather than the SQLAlchemy ORM because
SQLAlchemy has no native `vector` type without an extra dependency —
casting a Python list to Postgres `vector` via a plain string literal is
simpler and one less package to install.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session


def store_chunks(db: Session, document_id: str, chunks: list[str], embeddings: list[list[float]]) -> None:
    for i, (content, embedding) in enumerate(zip(chunks, embeddings)):
        vector_literal = "[" + ",".join(str(x) for x in embedding) + "]"
        db.execute(
            text(
                """
                insert into document_chunks (document_id, chunk_index, content, embedding)
                values (:document_id, :chunk_index, :content, cast(:embedding as vector))
                """
            ),
            {
                "document_id": document_id,
                "chunk_index": i,
                "content": content,
                "embedding": vector_literal,
            },
        )
    db.commit()


def get_similar_chunks(db: Session, document_id: str, query_embedding: list[float], top_k: int = 5) -> list[str]:
    """Cosine-similarity nearest-neighbor search, scoped to one document (used by Day 4 chatbot)."""
    vector_literal = "[" + ",".join(str(x) for x in query_embedding) + "]"
    rows = db.execute(
        text(
            """
            select content
            from document_chunks
            where document_id = :document_id
            order by embedding <=> cast(:embedding as vector)
            limit :top_k
            """
        ),
        {"document_id": document_id, "embedding": vector_literal, "top_k": top_k},
    ).fetchall()
    return [r[0] for r in rows]
