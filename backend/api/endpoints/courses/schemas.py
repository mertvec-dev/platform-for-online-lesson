"""Схемы для курсов"""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateCourse(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=60,
        description="Название курса",
        json_schema_extra={"example": "Подготовка к ЕГЭ по математике"},
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=300,
        description="Описание курса",
        json_schema_extra={
            "example": "Курс для регулярных онлайн-занятий по математике"
        },
    )


class UpdateCourse(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=60,
        description="Новое название курса",
    )
    description: str | None = Field(
        default=None,
        min_length=10,
        max_length=300,
        description="Новое описание курса",
    )
    is_active: bool | None = Field(
        default=None,
        description="Флаг активности курса",
    )


class CourseRead(BaseModel):
    id: int
    created_by_user_id: int
    title: str
    description: str
    slug: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CourseListItem(BaseModel):
    id: int
    title: str
    slug: str
    is_active: bool
    created_at: datetime
