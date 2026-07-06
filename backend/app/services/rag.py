from collections.abc import AsyncIterator

from app.services.gemini import GeminiService
from app.services.vector_store import VectorStore

TOP_K = 6

SYSTEM_PROMPT = (
    "You are a helpful study assistant. Answer the question using ONLY the provided "
    "context from the user's uploaded document(s). If the context doesn't contain the "
    "answer, say you don't know rather than guessing."
)


def build_prompt(question: str, context_chunks: list[dict]) -> str:
    context_text = "\n\n".join(
        f"[Page {c.get('page', '?')}] {c['text']}" for c in context_chunks
    ) or "(no relevant context found)"

    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"Context:\n{context_text}\n\n"
        f"Question: {question}\n\n"
        "Answer:"
    )


async def retrieve_context(
    gemini: GeminiService,
    vector_store: VectorStore,
    question: str,
    user_id: int,
    document_id: int | None,
) -> list[dict]:
    query_embedding = await gemini.embed_query(question)
    return vector_store.query(query_embedding, user_id=user_id, document_id=document_id, top_k=TOP_K)


async def stream_answer(
    gemini: GeminiService,
    vector_store: VectorStore,
    question: str,
    user_id: int,
    document_id: int | None,
) -> tuple[list[dict], AsyncIterator[str]]:
    sources = await retrieve_context(gemini, vector_store, question, user_id, document_id)
    prompt = build_prompt(question, sources)
    return sources, gemini.stream_text(prompt)
