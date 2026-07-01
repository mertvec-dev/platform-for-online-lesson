"""Схемы для логов посещения уроков (webhook-события LiveKit)"""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateLessonLog(BaseModel):
    lesson_id: int = Field(..., description="Идентификатор урока")
    user_id: int = Field(..., description="Идентификатор пользователя")
    session_id: str | None = Field(
        default=None,
        max_length=255,
        description="Идентификатор LiveKit-сессии",
    )
    joined_at: datetime | None = Field(default=None)


class UpdateLessonLog(BaseModel):
    left_at: datetime | None = Field(default=None)
    duration_seconds: int | None = Field(default=None, ge=0)
    session_id: str | None = Field(
        default=None,
        max_length=255,
        description="Идентификатор LiveKit-сессии для матчинга",
    )


class LessonLogRead(BaseModel):
    id: int
    lesson_id: int
    user_id: int
    session_id: str | None
    joined_at: datetime
    left_at: datetime | None
    duration_seconds: int | None
    webhook_received_at: datetime | None
    created_at: datetime
    updated_at: datetime


class LessonLogListItem(BaseModel):
    id: int
    lesson_id: int
    user_id: int
    session_id: str | None
    joined_at: datetime
    left_at: datetime | None
    duration_seconds: int | None


class BatchCreateLessonLogs(BaseModel):
    """Батч-создание логов (webhook-события от LiveKit)."""

    logs: list[CreateLessonLog] = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Список записей для массовой вставки",
    )
