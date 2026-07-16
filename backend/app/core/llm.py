import json

from groq import Groq

from app.core.config import settings

_client = Groq(api_key=settings.groq_api_key)

COURSE_GENERATION_SYSTEM_PROMPT = """You are an expert instructional designer. Given raw text extracted \
from a document, produce a structured e-course as STRICT JSON only — no markdown fences, no preamble, \
no commentary, just a single valid JSON object matching exactly this shape:

{
  "title": "string",
  "description": "string",
  "estimated_time_minutes": 0,
  "difficulty_level": "beginner | intermediate | advanced",
  "learning_objectives": ["string", "..."],
  "prerequisites": ["string", "..."],
  "chapters": [
    {
      "title": "string",
      "summary": "string",
      "lessons": [
        {
          "title": "string",
          "content_markdown": "string (well-structured explanation, 150-400 words, markdown formatted)",
          "key_takeaways": ["string", "..."],
          "important_notes": ["string", "..."],
          "real_world_examples": ["string", "..."],
          "summary": "string"
        }
      ]
    }
  ]
}

Rules:
- Produce 3-6 chapters, each with 2-5 lessons. Keep it proportional to how much distinct content the \
source text actually contains — do not pad with filler.
- Base everything strictly on the provided text. Do not invent facts not supported by it.
- Return ONLY the JSON object, nothing else.
"""


def generate_course_structure(source_text: str) -> dict:
    """Calls Groq to turn extracted document text into a structured course. Returns parsed dict."""
    # Guard against exceeding context window on very large PDFs — truncate to a
    # generous but safe budget. Full-text RAG chatbot (Day 4) still sees everything
    # via document_chunks; this is only for the course-structure generation pass.
    max_chars = 60000
    truncated = source_text[:max_chars]

    response = _client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": COURSE_GENERATION_SYSTEM_PROMPT},
            {"role": "user", "content": truncated},
        ],
        temperature=0.3,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    return json.loads(raw)
