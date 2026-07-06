from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.models import Flashcard, FlashcardDeck, User
from app.db.session import get_db
from app.schemas.flashcards import FlashcardDeckResponse, FlashcardGenerateRequest
from app.services.flashcards import generate_flashcards
from app.services.gemini import GeminiService, get_gemini_service
from app.services.ingestion import get_document_or_none
from app.services.vector_store import VectorStore, get_vector_store

router = APIRouter(tags=["flashcards"])


@router.post(
    "/api/documents/{document_id}/flashcards",
    response_model=FlashcardDeckResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_flashcard_deck(
    document_id: int,
    payload: FlashcardGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    gemini: GeminiService = Depends(get_gemini_service),
    vector_store: VectorStore = Depends(get_vector_store),
) -> FlashcardDeck:
    document = await get_document_or_none(db, document_id, current_user.id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    try:
        result = await generate_flashcards(
            gemini, vector_store, document_id, current_user.id, payload.topic, payload.num_cards
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    deck = FlashcardDeck(
        user_id=current_user.id,
        document_id=document_id,
        title=payload.topic or document.title,
    )
    deck.flashcards = [
        Flashcard(term=card.term, definition=card.definition, position=i)
        for i, card in enumerate(result.flashcards)
    ]
    db.add(deck)
    await db.commit()
    await db.refresh(deck, attribute_names=["flashcards"])
    return deck


@router.get("/api/flashcard-decks", response_model=list[FlashcardDeckResponse])
async def list_flashcard_decks(
    document_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[FlashcardDeck]:
    stmt = (
        select(FlashcardDeck)
        .where(FlashcardDeck.user_id == current_user.id)
        .options(selectinload(FlashcardDeck.flashcards))
    )
    if document_id is not None:
        stmt = stmt.where(FlashcardDeck.document_id == document_id)
    stmt = stmt.order_by(FlashcardDeck.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/api/flashcard-decks/{deck_id}", response_model=FlashcardDeckResponse)
async def get_flashcard_deck(
    deck_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FlashcardDeck:
    stmt = (
        select(FlashcardDeck)
        .where(FlashcardDeck.id == deck_id, FlashcardDeck.user_id == current_user.id)
        .options(selectinload(FlashcardDeck.flashcards))
    )
    result = await db.execute(stmt)
    deck = result.scalar_one_or_none()
    if deck is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flashcard deck not found")
    return deck
