from app.services.gemini import GeminiService
from app.services.quiz import build_context
from app.services.vector_store import VectorStore


def build_prompt(context: str) -> str:
    return (
        "You are a study assistant. Write a concise summary of the following document "
        "content, capturing the main points and key ideas in a few short paragraphs.\n\n"
        f"Context:\n{context}"
    )


async def summarize_document(
    gemini: GeminiService,
    vector_store: VectorStore,
    document_id: int,
    user_id: int,
) -> str:
    chunks = vector_store.get_document_chunks(document_id, user_id)
    if not chunks:
        raise ValueError("This document has no ingested content to summarize")

    context = build_context(chunks)
    prompt = build_prompt(context)
    return await gemini.generate_text(prompt)
