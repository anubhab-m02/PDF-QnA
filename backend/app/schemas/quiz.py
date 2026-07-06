from datetime import datetime

from pydantic import BaseModel, Field


class QuizGenerateRequest(BaseModel):
    topic: str = ""
    num_questions: int = Field(default=5, ge=1, le=20)


class QuizResponse(BaseModel):
    id: int
    document_id: int
    topic: str
    questions: list[dict]
    created_at: datetime


class QuizAttemptCreate(BaseModel):
    answers: list[int]


class QuizAttemptResponse(BaseModel):
    id: int
    quiz_id: int
    answers: list[int]
    score: int
    total: int
    created_at: datetime
