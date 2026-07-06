from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    filename: str
    title: str
    page_count: int
    chunk_count: int
    status: str
    error: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
