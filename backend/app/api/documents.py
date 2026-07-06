from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.deps import get_current_user
from app.db.models import Document, DocumentStatus, User
from app.db.session import get_db, get_session_factory
from app.schemas.documents import DocumentResponse
from app.services.gemini import GeminiService, get_gemini_service
from app.services.ingestion import get_document_or_none, ingest_document, sha256_bytes
from app.services.vector_store import VectorStore, get_vector_store

router = APIRouter(prefix="/api/documents", tags=["documents"])

MAX_UPLOAD_BYTES = 50 * 1024 * 1024


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    gemini: GeminiService = Depends(get_gemini_service),
    vector_store: VectorStore = Depends(get_vector_store),
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> Document:
    if file.content_type not in ("application/pdf", "application/x-pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are accepted")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
    if len(pdf_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File exceeds 50MB limit")

    digest = sha256_bytes(pdf_bytes)

    document = Document(
        user_id=current_user.id,
        filename=file.filename or "document.pdf",
        title=(file.filename or "document.pdf").rsplit(".", 1)[0],
        sha256=digest,
        status=DocumentStatus.processing.value,
    )
    db.add(document)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This document has already been uploaded")
    await db.refresh(document)

    background_tasks.add_task(
        ingest_document,
        document.id,
        pdf_bytes,
        session_factory,
        gemini,
        vector_store,
    )

    return document


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Document]:
    result = await db.execute(
        select(Document).where(Document.user_id == current_user.id).order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Document:
    document = await get_document_or_none(db, document_id, current_user.id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    vector_store: VectorStore = Depends(get_vector_store),
) -> None:
    document = await get_document_or_none(db, document_id, current_user.id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    vector_store.delete_document(document_id)
    await db.delete(document)
    await db.commit()
