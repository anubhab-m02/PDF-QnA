class FakeGeminiService:
    """Deterministic stand-in for GeminiService — no network calls."""

    def __init__(self):
        self.chat_model = "fake-chat-model"
        self.embedding_model = "fake-embedding-model"
        self.embedding_dims = 8

    async def embed_texts(self, texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
        return [[float(len(t) % 7)] * self.embedding_dims for t in texts]

    async def embed_query(self, text: str) -> list[float]:
        results = await self.embed_texts([text])
        return results[0]

    async def generate_text(self, prompt: str) -> str:
        return "fake response"

    async def generate_structured(self, prompt: str, response_schema: type) -> str:
        import json

        schema_name = getattr(response_schema, "__name__", "")
        if schema_name == "QuizGenerationResult":
            return json.dumps(
                {
                    "questions": [
                        {
                            "question": f"Fake question {i}?",
                            "options": ["A", "B", "C", "D"],
                            "answer_index": 0,
                            "explanation": "Because fake.",
                        }
                        for i in range(1, 4)
                    ]
                }
            )
        if schema_name == "FlashcardGenerationResult":
            return json.dumps(
                {
                    "flashcards": [
                        {"term": f"Term {i}", "definition": f"Definition {i}"}
                        for i in range(1, 4)
                    ]
                }
            )
        return "{}"

    async def stream_text(self, prompt: str):
        for token in ["fake ", "streamed ", "response"]:
            yield token


class FakeVectorStore:
    """In-memory stand-in for VectorStore — no filesystem/Chroma dependency."""

    def __init__(self):
        self._chunks: dict[str, dict] = {}

    def add_chunks(self, ids, embeddings, documents, metadatas) -> None:
        for id_, doc, meta in zip(ids, documents, metadatas):
            self._chunks[id_] = {"text": doc, **meta}

    def query(self, query_embedding, user_id, document_id=None, top_k=6) -> list[dict]:
        hits = [
            c for c in self._chunks.values()
            if c["user_id"] == user_id and (document_id is None or c["document_id"] == document_id)
        ]
        return hits[:top_k]

    def delete_document(self, document_id: int) -> None:
        to_remove = [k for k, v in self._chunks.items() if v["document_id"] == document_id]
        for k in to_remove:
            del self._chunks[k]

    def get_document_chunks(self, document_id: int, user_id: int, limit: int = 40) -> list[dict]:
        hits = [
            c for c in self._chunks.values()
            if c["user_id"] == user_id and c["document_id"] == document_id
        ]
        return hits[:limit]
