import json

from pydantic import BaseModel

from app.services.gemini import GeminiService
from app.services.quiz import build_context
from app.services.vector_store import VectorStore


class FlashcardItem(BaseModel):
    term: str
    definition: str


class FlashcardGenerationResult(BaseModel):
    flashcards: list[FlashcardItem]


def build_prompt(context: str, topic: str, num_cards: int) -> str:
    topic_line = f"Focus on the topic: {topic}.\n" if topic else ""
    return (
        f"You are a flashcard generator for a study assistant. Using ONLY the context "
        f"below, generate exactly {num_cards} flashcards, each with a short term/concept "
        f"and a clear, concise definition.\n"
        f"{topic_line}\n"
        f"Context:\n{context}"
    )


async def generate_flashcards(
    gemini: GeminiService,
    vector_store: VectorStore,
    document_id: int,
    user_id: int,
    topic: str = "",
    num_cards: int = 10,
) -> FlashcardGenerationResult:
    chunks = vector_store.get_document_chunks(document_id, user_id)
    if not chunks:
        raise ValueError("This document has no ingested content to generate flashcards from")

    context = build_context(chunks)
    prompt = build_prompt(context, topic, num_cards)

    raw = await gemini.generate_structured(prompt, FlashcardGenerationResult)
    data = json.loads(raw)
    return FlashcardGenerationResult.model_validate(data)
