from datetime import datetime

from pydantic import BaseModel, Field


class FlashcardGenerateRequest(BaseModel):
    topic: str = ""
    num_cards: int = Field(default=10, ge=1, le=30)


class FlashcardItemResponse(BaseModel):
    id: int
    term: str
    definition: str
    position: int

    model_config = {"from_attributes": True}


class FlashcardDeckResponse(BaseModel):
    id: int
    document_id: int
    title: str
    created_at: datetime
    flashcards: list[FlashcardItemResponse]

    model_config = {"from_attributes": True}
