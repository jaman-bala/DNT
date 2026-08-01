from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NoteCreateDTO(BaseModel):
    title: str = Field(
        ..., max_length=255, description="Note title", example="Shopping list"
    )
    content: str = Field("", description="Note content", example="Milk, eggs, bread")


class NoteUpdateDTO(BaseModel):
    title: str | None = Field(None, max_length=255, description="Note title")
    content: str | None = Field(None, description="Note content")


class NoteResponseDTO(BaseModel):
    id: UUID = Field(..., description="Note ID")
    title: str = Field(..., description="Note title")
    content: str = Field(..., description="Note content")
    created_at: datetime = Field(..., description="Creation date")
    updated_at: datetime = Field(..., description="Last update date")

    model_config = ConfigDict(from_attributes=True)
