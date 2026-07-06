from functools import lru_cache

import chromadb

from app.core.config import get_settings

COLLECTION_NAME = "document_chunks"


class VectorStore:
    def __init__(self, persist_dir: str):
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection(name=COLLECTION_NAME)

    def add_chunks(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict],
    ) -> None:
        if not ids:
            return
        self._collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

    def query(
        self,
        query_embedding: list[float],
        user_id: int,
        document_id: int | None = None,
        top_k: int = 6,
    ) -> list[dict]:
        where: dict = {"user_id": user_id}
        if document_id is not None:
            where = {"$and": [{"user_id": user_id}, {"document_id": document_id}]}

        result = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
        )
        hits: list[dict] = []
        docs = result.get("documents") or [[]]
        metas = result.get("metadatas") or [[]]
        for doc, meta in zip(docs[0], metas[0]):
            hits.append({"text": doc, **meta})
        return hits

    def delete_document(self, document_id: int) -> None:
        self._collection.delete(where={"document_id": document_id})

    def get_document_chunks(self, document_id: int, user_id: int, limit: int = 40) -> list[dict]:
        """Fetch a representative sample of a document's chunks (no similarity search —
        used for tasks like quiz/flashcard/summary generation that need broad coverage
        rather than a query-relevant subset)."""
        result = self._collection.get(
            where={"$and": [{"user_id": user_id}, {"document_id": document_id}]},
            limit=limit,
        )
        hits: list[dict] = []
        docs = result.get("documents") or []
        metas = result.get("metadatas") or []
        for doc, meta in zip(docs, metas):
            hits.append({"text": doc, **meta})
        return hits


@lru_cache
def get_vector_store() -> VectorStore:
    settings = get_settings()
    return VectorStore(persist_dir=settings.chroma_dir)
