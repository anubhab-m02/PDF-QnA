from datetime import datetime

from pydantic import BaseModel


class ChatSessionCreate(BaseModel):
    document_id: int | None = None
    title: str = "New chat"


class ChatSessionResponse(BaseModel):
    id: int
    document_id: int | None
    title: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    sources_json: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
