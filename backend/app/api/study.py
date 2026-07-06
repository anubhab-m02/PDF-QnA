from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import (
    ChatSession,
    Document,
    DocumentStatus,
    FlashcardDeck,
    Message,
    Quiz,
    QuizAttempt,
    User,
)
from app.db.session import get_db
from app.schemas.study import ProfileStatsResponse, SummaryResponse
from app.services.gemini import GeminiService, get_gemini_service
from app.services.ingestion import get_document_or_none
from app.services.summary import summarize_document
from app.services.vector_store import VectorStore, get_vector_store

router = APIRouter(tags=["study"])


@router.post("/api/documents/{document_id}/summary", response_model=SummaryResponse)
async def create_summary(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    gemini: GeminiService = Depends(get_gemini_service),
    vector_store: VectorStore = Depends(get_vector_store),
) -> SummaryResponse:
    document = await get_document_or_none(db, document_id, current_user.id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    try:
        summary = await summarize_document(gemini, vector_store, document_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return SummaryResponse(document_id=document_id, summary=summary)


async def _scalar_count(db: AsyncSession, stmt) -> int:
    result = await db.execute(stmt)
    return result.scalar_one()


@router.get("/api/profile/stats", response_model=ProfileStatsResponse)
async def get_profile_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProfileStatsResponse:
    uid = current_user.id

    document_count = await _scalar_count(
        db, select(func.count()).select_from(Document).where(Document.user_id == uid)
    )
    ready_document_count = await _scalar_count(
        db,
        select(func.count())
        .select_from(Document)
        .where(Document.user_id == uid, Document.status == DocumentStatus.ready.value),
    )
    chat_session_count = await _scalar_count(
        db, select(func.count()).select_from(ChatSession).where(ChatSession.user_id == uid)
    )
    message_count = await _scalar_count(
        db,
        select(func.count())
        .select_from(Message)
        .join(ChatSession, Message.session_id == ChatSession.id)
        .where(ChatSession.user_id == uid),
    )
    quiz_count = await _scalar_count(
        db, select(func.count()).select_from(Quiz).where(Quiz.user_id == uid)
    )
    quiz_attempt_count = await _scalar_count(
        db, select(func.count()).select_from(QuizAttempt).where(QuizAttempt.user_id == uid)
    )
    flashcard_deck_count = await _scalar_count(
        db, select(func.count()).select_from(FlashcardDeck).where(FlashcardDeck.user_id == uid)
    )

    avg_result = await db.execute(
        select(func.sum(QuizAttempt.score), func.sum(QuizAttempt.total)).where(
            QuizAttempt.user_id == uid
        )
    )
    score_sum, total_sum = avg_result.one()
    average_quiz_score_pct = (score_sum / total_sum * 100) if total_sum else None

    return ProfileStatsResponse(
        document_count=document_count,
        ready_document_count=ready_document_count,
        chat_session_count=chat_session_count,
        message_count=message_count,
        quiz_count=quiz_count,
        quiz_attempt_count=quiz_attempt_count,
        average_quiz_score_pct=average_quiz_score_pct,
        flashcard_deck_count=flashcard_deck_count,
    )
