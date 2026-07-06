import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import Quiz, QuizAttempt, User
from app.db.session import get_db
from app.services.gemini import GeminiService, get_gemini_service
from app.services.ingestion import get_document_or_none
from app.services.quiz import generate_quiz, score_attempt
from app.services.vector_store import VectorStore, get_vector_store
from app.schemas.quiz import (
    QuizAttemptCreate,
    QuizAttemptResponse,
    QuizGenerateRequest,
    QuizResponse,
)

router = APIRouter(tags=["quiz"])


def _to_quiz_response(quiz: Quiz) -> QuizResponse:
    return QuizResponse(
        id=quiz.id,
        document_id=quiz.document_id,
        topic=quiz.topic,
        questions=json.loads(quiz.questions_json),
        created_at=quiz.created_at,
    )


def _to_attempt_response(attempt: QuizAttempt) -> QuizAttemptResponse:
    return QuizAttemptResponse(
        id=attempt.id,
        quiz_id=attempt.quiz_id,
        answers=json.loads(attempt.answers_json),
        score=attempt.score,
        total=attempt.total,
        created_at=attempt.created_at,
    )


@router.post(
    "/api/documents/{document_id}/quizzes",
    response_model=QuizResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_quiz(
    document_id: int,
    payload: QuizGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    gemini: GeminiService = Depends(get_gemini_service),
    vector_store: VectorStore = Depends(get_vector_store),
) -> QuizResponse:
    document = await get_document_or_none(db, document_id, current_user.id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    try:
        result = await generate_quiz(
            gemini, vector_store, document_id, current_user.id, payload.topic, payload.num_questions
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    quiz = Quiz(
        user_id=current_user.id,
        document_id=document_id,
        topic=payload.topic,
        questions_json=json.dumps([q.model_dump() for q in result.questions]),
    )
    db.add(quiz)
    await db.commit()
    await db.refresh(quiz)
    return _to_quiz_response(quiz)


@router.get("/api/quizzes", response_model=list[QuizResponse])
async def list_quizzes(
    document_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[QuizResponse]:
    stmt = select(Quiz).where(Quiz.user_id == current_user.id)
    if document_id is not None:
        stmt = stmt.where(Quiz.document_id == document_id)
    stmt = stmt.order_by(Quiz.created_at.desc())
    result = await db.execute(stmt)
    return [_to_quiz_response(q) for q in result.scalars().all()]


@router.get("/api/quizzes/{quiz_id}", response_model=QuizResponse)
async def get_quiz(
    quiz_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuizResponse:
    quiz = await db.get(Quiz, quiz_id)
    if quiz is None or quiz.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    return _to_quiz_response(quiz)


@router.post(
    "/api/quizzes/{quiz_id}/attempts",
    response_model=QuizAttemptResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_attempt(
    quiz_id: int,
    payload: QuizAttemptCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuizAttemptResponse:
    quiz = await db.get(Quiz, quiz_id)
    if quiz is None or quiz.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

    questions = json.loads(quiz.questions_json)
    score, total = score_attempt(questions, payload.answers)

    attempt = QuizAttempt(
        quiz_id=quiz.id,
        user_id=current_user.id,
        answers_json=json.dumps(payload.answers),
        score=score,
        total=total,
    )
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)
    return _to_attempt_response(attempt)
