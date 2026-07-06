from pydantic import BaseModel


class SummaryResponse(BaseModel):
    document_id: int
    summary: str


class ProfileStatsResponse(BaseModel):
    document_count: int
    ready_document_count: int
    chat_session_count: int
    message_count: int
    quiz_count: int
    quiz_attempt_count: int
    average_quiz_score_pct: float | None
    flashcard_deck_count: int
