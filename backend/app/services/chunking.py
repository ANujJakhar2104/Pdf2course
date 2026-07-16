"""
Splits long extracted text into overlapping chunks suitable for embedding.

Simple word-based chunker (no extra NLP deps needed). Overlap keeps context
from being cut off mid-idea at chunk boundaries, which matters for retrieval
quality in the RAG chatbot later.
"""

CHUNK_SIZE_WORDS = 220
CHUNK_OVERLAP_WORDS = 40


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE_WORDS, overlap: int = CHUNK_OVERLAP_WORDS) -> list[str]:
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end >= len(words):
            break
        start = end - overlap  # step back for overlap

    return chunks
