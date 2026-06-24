"""Схемы для уроков"""

from datetime import datetime

from pydantic import BaseModel, Field

from ...models.lessons import LessonStatus


class CreateLesson(BaseModel):
    room_id: int = Field(..., description="Идентификатор комнаты")
    title: str = Field(
        ...,
        min_length=1,
        max_length=60,
        description="Название урока",
        json_schema_extra={"example": "Урок по теме квадратных уравнений"},
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=300,
        description="Описание урока",
        json_schema_extra={"example": "Разбор квадратных уравнений и дискриминанта"},
    )
    max_participants: int = Field(
        default=50,
        ge=1,
        le=50,
        description="Максимальное количество участников урока",
    )
    scheduled_at: datetime = Field(
        ...,
        description="Плановое время начала урока",
    )


class UpdateLesson(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=60,
        description="Новое название урока",
    )
    description: str | None = Field(
        default=None,
        min_length=10,
        max_length=300,
        description="Новое описание урока",
    )
    max_participants: int | None = Field(
        default=None,
        ge=1,
        le=50,
        description="Новое ограничение участников",
    )
    scheduled_at: datetime | None = Field(
        default=None,
        description="Новое плановое время начала урока",
    )
    status: LessonStatus | None = Field(
        default=None,
        description="Статус урока",
    )


class StartLessonRequest(BaseModel):
    started_at: datetime | None = Field(
        default=None,
        description="Фактическое время старта урока. Если не передано, сервер может поставить текущее время.",
    )


class EndLessonRequest(BaseModel):
    ended_at: datetime | None = Field(
        default=None,
        description="Фактическое время завершения урока. Если не передано, сервер может поставить текущее время.",
    )


class LessonRead(BaseModel):
    id: int
    room_id: int
    title: str
    description: str
    max_participants: int
    status: LessonStatus
    scheduled_at: datetime
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime
    updated_at: datetime


class LessonListItem(BaseModel):
    id: int
    room_id: int
    title: str
    status: LessonStatus
    scheduled_at: datetime
    started_at: datetime | None
    ended_at: datetime | None
