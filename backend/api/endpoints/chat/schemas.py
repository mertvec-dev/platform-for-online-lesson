"""Схемы для сообщений чата"""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateChatMessage(BaseModel):
    room_id: int = Field(..., description="Идентификатор комнаты")
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
    room_id: int
    author_id: int
    text: str
    created_at: datetime
    updated_at: datetime


class ChatMessageListItem(BaseModel):
    id: int
    author_id: int
    text: str
    created_at: datetime
