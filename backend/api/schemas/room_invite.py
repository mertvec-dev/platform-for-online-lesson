"""Схемы для invite-ссылок комнат"""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateRoomInvite(BaseModel):
    room_id: int = Field(..., description="Идентификатор комнаты")
    max_uses: int | None = Field(
        default=None,
        gt=0,
        description="Максимальное число использований invite-ссылки",
    )
    expires_at: datetime | None = Field(
        default=None,
        description="Время истечения invite-ссылки",
    )


class UpdateRoomInvite(BaseModel):
    is_active: bool | None = Field(
        default=None,
        description="Флаг активности invite-ссылки",
    )
    max_uses: int | None = Field(
        default=None,
        gt=0,
        description="Новое максимальное число использований",
    )
    expires_at: datetime | None = Field(
        default=None,
        description="Новое время истечения invite-ссылки",
    )


class JoinRoomByInvite(BaseModel):
    token: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Токен invite-ссылки",
    )


class RoomInviteRead(BaseModel):
    id: int
    room_id: int
    created_by_user_id: int
    token: str
    is_active: bool
    max_uses: int | None
    used_count: int
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime


class RoomInviteListItem(BaseModel):
    id: int
    room_id: int
    token: str
    is_active: bool
    used_count: int
    expires_at: datetime | None
