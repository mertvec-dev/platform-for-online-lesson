"""Схемы для логов посещения уроков"""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateLessonLog(BaseModel):
    lesson_id: int = Field(..., description="Идентификатор урока")
    user_id: int = Field(..., description="Идентификатор пользователя")
    joined_at: datetime | None = Field(
        default=None,
        description="Время входа на урок",
    )


class UpdateLessonLog(BaseModel):
    left_at: datetime | None = Field(
        default=None,
        description="Время выхода с урока",
    )
    duration_seconds: int | None = Field(
        default=None,
        ge=0,
        description="Длительность присутствия в секундах",
    )


class LessonLogRead(BaseModel):
    id: int
    lesson_id: int
    user_id: int
    joined_at: datetime
    left_at: datetime | None
    duration_seconds: int | None
    created_at: datetime
    updated_at: datetime


class LessonLogListItem(BaseModel):
    id: int
    lesson_id: int
    user_id: int
    joined_at: datetime
    left_at: datetime | None
    duration_seconds: int | None
