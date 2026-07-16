"""
Generates embeddings locally using sentence-transformers (free, no API cost).
Model: all-MiniLM-L6-v2 -> 384-dim vectors, matches the `vector(384)` column
in document_chunks (see schema.sql).
"""

from functools import lru_cache


@lru_cache(maxsize=1)
def _get_model():
    # Imported lazily so the app can start even before the (largish) model
    # dependency is downloaded on first use.
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("all-MiniLM-L6-v2")


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    model = _get_model()
    vectors = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return [v.tolist() for v in vectors]


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]
