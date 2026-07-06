import json

from pydantic import BaseModel, Field

from app.services.gemini import GeminiService
from app.services.vector_store import VectorStore

MAX_CONTEXT_CHARS = 12000


class QuizQuestion(BaseModel):
    question: str
    options: list[str] = Field(min_length=4, max_length=4)
    answer_index: int = Field(ge=0, le=3)
    explanation: str


class QuizGenerationResult(BaseModel):
    questions: list[QuizQuestion]


def build_context(chunks: list[dict], max_chars: int = MAX_CONTEXT_CHARS) -> str:
    parts: list[str] = []
    total = 0
    for c in chunks:
        text = c["text"]
        if total + len(text) > max_chars:
            break
        parts.append(text)
        total += len(text)
    return "\n\n".join(parts)


def build_prompt(context: str, topic: str, num_questions: int) -> str:
    topic_line = f"Focus on the topic: {topic}.\n" if topic else ""
    return (
        f"You are a quiz generator for a study assistant. Using ONLY the context below, "
        f"generate exactly {num_questions} multiple-choice questions with 4 options each, "
        f"the index of the correct option, and a short explanation for why it's correct.\n"
        f"{topic_line}\n"
        f"Context:\n{context}"
    )


async def generate_quiz(
    gemini: GeminiService,
    vector_store: VectorStore,
    document_id: int,
    user_id: int,
    topic: str = "",
    num_questions: int = 5,
) -> QuizGenerationResult:
    chunks = vector_store.get_document_chunks(document_id, user_id)
    if not chunks:
        raise ValueError("This document has no ingested content to generate a quiz from")

    context = build_context(chunks)
    prompt = build_prompt(context, topic, num_questions)

    raw = await gemini.generate_structured(prompt, QuizGenerationResult)
    data = json.loads(raw)
    return QuizGenerationResult.model_validate(data)


def score_attempt(questions: list[dict], answers: list[int]) -> tuple[int, int]:
    total = len(questions)
    score = sum(
        1
        for q, a in zip(questions, answers)
        if a == q.get("answer_index")
    )
    return score, total
