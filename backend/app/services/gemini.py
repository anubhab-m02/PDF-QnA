from collections.abc import AsyncIterator
from functools import lru_cache

from google import genai
from google.genai import types

from app.core.config import get_settings

EMBED_BATCH_SIZE = 100


class GeminiService:
    def __init__(self, api_key: str, chat_model: str, embedding_model: str, embedding_dims: int):
        self._client = genai.Client(api_key=api_key)
        self.chat_model = chat_model
        self.embedding_model = embedding_model
        self.embedding_dims = embedding_dims

    async def embed_texts(self, texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
        if not texts:
            return []

        embeddings: list[list[float]] = []
        for i in range(0, len(texts), EMBED_BATCH_SIZE):
            batch = texts[i : i + EMBED_BATCH_SIZE]
            result = await self._client.aio.models.embed_content(
                model=self.embedding_model,
                contents=batch,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=self.embedding_dims,
                ),
            )
            embeddings.extend(e.values for e in result.embeddings)
        return embeddings

    async def embed_query(self, text: str) -> list[float]:
        results = await self.embed_texts([text], task_type="RETRIEVAL_QUERY")
        return results[0]

    async def generate_text(self, prompt: str) -> str:
        response = await self._client.aio.models.generate_content(
            model=self.chat_model,
            contents=prompt,
        )
        return response.text or ""

    async def generate_structured(self, prompt: str, response_schema: type) -> str:
        response = await self._client.aio.models.generate_content(
            model=self.chat_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
            ),
        )
        return response.text or ""

    async def stream_text(self, prompt: str) -> AsyncIterator[str]:
        stream = await self._client.aio.models.generate_content_stream(
            model=self.chat_model,
            contents=prompt,
        )
        async for chunk in stream:
            if chunk.text:
                yield chunk.text


@lru_cache
def get_gemini_service() -> GeminiService:
    settings = get_settings()
    return GeminiService(
        api_key=settings.google_api_key,
        chat_model=settings.gemini_chat_model,
        embedding_model=settings.gemini_embedding_model,
        embedding_dims=settings.gemini_embedding_dims,
    )
