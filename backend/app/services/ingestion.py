import hashlib
import logging

from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import Document, DocumentStatus
from app.services.chunking import chunk_pages
from app.services.gemini import GeminiService
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_pages(pdf_bytes: bytes) -> list[str]:
    import io

    reader = PdfReader(io.BytesIO(pdf_bytes))
    return [page.extract_text() or "" for page in reader.pages]


async def ingest_document(
    document_id: int,
    pdf_bytes: bytes,
    session_factory: async_sessionmaker[AsyncSession],
    gemini: GeminiService,
    vector_store: VectorStore,
) -> None:
    async with session_factory() as db:
        document = await db.get(Document, document_id)
        if document is None:
            logger.error("ingest_document: document %s not found", document_id)
            return

        try:
            pages = extract_pages(pdf_bytes)
            chunks = chunk_pages(pages)

            if not chunks:
                raise ValueError("No extractable text found in this PDF")

            texts = [c.text for c in chunks]
            embeddings = await gemini.embed_texts(texts)

            ids = [f"{document_id}-{i}" for i in range(len(chunks))]
            metadatas = [
                {"document_id": document_id, "user_id": document.user_id, "page": c.page}
                for c in chunks
            ]
            vector_store.add_chunks(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

            document.page_count = len(pages)
            document.chunk_count = len(chunks)
            document.status = DocumentStatus.ready.value
            document.error = None
        except Exception as exc:  # noqa: BLE001 - persisted as a safe status, not swallowed
            logger.exception("ingestion failed for document %s", document_id)
            document.status = DocumentStatus.failed.value
            document.error = str(exc)[:500]

        await db.commit()


async def get_document_or_none(db: AsyncSession, document_id: int, user_id: int) -> Document | None:
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == user_id)
    )
    return result.scalar_one_or_none()
