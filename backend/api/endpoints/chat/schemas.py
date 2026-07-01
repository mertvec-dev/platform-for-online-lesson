"""Схемы для сообщений чата"""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateChatMessage(BaseModel):
    course_id: int = Field(..., description="Идентификатор курса")
    text: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Текст сообщения",
    )


class UpdateChatMessage(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Обновленный текст сообщения",
    )


class ChatMessageRead(BaseModel):
    id: int
    course_id: int
    author_id: int
    text: str
    created_at: datetime
    updated_at: datetime


class ChatMessageListItem(BaseModel):
    id: int
    author_id: int
    text: str
    created_at: datetime
