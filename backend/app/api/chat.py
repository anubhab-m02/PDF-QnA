import json

from fastapi import APIRouter, Depends, HTTPException, status
from sse_starlette.sse import EventSourceResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import ChatSession, Document, Message, MessageRole, User
from app.db.session import get_db
from app.schemas.chat import ChatSessionCreate, ChatSessionResponse, MessageCreate, MessageResponse
from app.services.gemini import GeminiService, get_gemini_service
from app.services.rag import stream_answer
from app.services.vector_store import VectorStore, get_vector_store

router = APIRouter(prefix="/api/chat", tags=["chat"])


async def _get_session_or_404(db: AsyncSession, session_id: int, user_id: int) -> ChatSession:
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    return session


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: ChatSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatSession:
    if payload.document_id is not None:
        doc = await db.get(Document, payload.document_id)
        if doc is None or doc.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    session = ChatSession(user_id=current_user.id, document_id=payload.document_id, title=payload.title)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/sessions", response_model=list[ChatSessionResponse])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChatSession]:
    result = await db.execute(
        select(ChatSession).where(ChatSession.user_id == current_user.id).order_by(ChatSession.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/sessions/{session_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Message]:
    session = await _get_session_or_404(db, session_id, current_user.id)
    result = await db.execute(select(Message).where(Message.session_id == session.id).order_by(Message.id))
    return list(result.scalars().all())


@router.post("/sessions/{session_id}/messages")
async def post_message(
    session_id: int,
    payload: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    gemini: GeminiService = Depends(get_gemini_service),
    vector_store: VectorStore = Depends(get_vector_store),
) -> EventSourceResponse:
    session = await _get_session_or_404(db, session_id, current_user.id)

    user_message = Message(session_id=session.id, role=MessageRole.user.value, content=payload.content)
    db.add(user_message)
    await db.commit()

    sources, token_stream = await stream_answer(
        gemini, vector_store, payload.content, current_user.id, session.document_id
    )

    async def event_generator():
        full_text = ""
        async for token in token_stream:
            full_text += token
            yield {"event": "token", "data": token}

        assistant_message = Message(
            session_id=session.id,
            role=MessageRole.assistant.value,
            content=full_text,
            sources_json=json.dumps(sources),
        )
        db.add(assistant_message)
        await db.commit()
        await db.refresh(assistant_message)

        yield {
            "event": "done",
            "data": json.dumps({"message_id": assistant_message.id, "sources": sources}),
        }

    return EventSourceResponse(event_generator())
