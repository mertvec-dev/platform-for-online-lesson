"""Схемы для уроков"""

from datetime import datetime

from pydantic import BaseModel, Field

from .....models.lessons import LessonStatus


class CreateLesson(BaseModel):
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
        description="Максимальное количество участников",
    )
    scheduled_at: datetime = Field(
        ...,
        description="Плановое время начала урока",
    )
    duration_minutes: int = Field(
        default=60,
        ge=1,
        le=480,
        description="Плановая длительность урока в минутах",
    )


class UpdateLesson(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=60)
    description: str | None = Field(default=None, min_length=10, max_length=300)
    max_participants: int | None = Field(default=None, ge=1, le=50)
    scheduled_at: datetime | None = Field(default=None)
    duration_minutes: int | None = Field(default=None, ge=1, le=480)


class UpdateStatus(BaseModel):
    status: LessonStatus | None = Field(default=None)


class StartLessonRequest(BaseModel):
    started_at: datetime | None = Field(default=None)


class EndLessonRequest(BaseModel):
    ended_at: datetime | None = Field(default=None)


class LessonRead(BaseModel):
    id: int
    course_id: int
    title: str
    description: str
    max_participants: int
    status: LessonStatus
    scheduled_at: datetime
    duration_minutes: int
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime
    updated_at: datetime


class LessonListItem(BaseModel):
    id: int
    course_id: int
    title: str
    status: LessonStatus
    scheduled_at: datetime
    duration_minutes: int
    started_at: datetime | None
    ended_at: datetime | None
