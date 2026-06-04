"""Схемы для комнат"""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateRoom(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=60,
        description="Название комнаты",
        json_schema_extra={"example": "Подготовка к ЕГЭ по математике"},
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=300,
        description="Описание комнаты",
        json_schema_extra={
            "example": "Комната для регулярных онлайн-занятий по математике"
        },
    )


class UpdateRoom(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=60,
        description="Новое название комнаты",
    )
    description: str | None = Field(
        default=None,
        min_length=10,
        max_length=300,
        description="Новое описание комнаты",
    )
    is_active: bool | None = Field(
        default=None,
        description="Флаг активности комнаты",
    )


class RoomRead(BaseModel):
    id: int
    created_by_user_id: int
    title: str
    description: str
    slug: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RoomListItem(BaseModel):
    id: int
    title: str
    slug: str
    is_active: bool
    created_at: datetime
