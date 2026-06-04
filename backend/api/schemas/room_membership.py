"""Схемы для membership комнат"""

from datetime import datetime

from pydantic import BaseModel, Field


class AddRoomMembership(BaseModel):
    room_id: int = Field(..., description="Идентификатор комнаты")
    user_id: int = Field(..., description="Идентификатор пользователя")
    invite_id: int | None = Field(
        default=None,
        description="Идентификатор invite, через который пользователь был добавлен",
    )
    added_via_invite_link: bool = Field(
        default=False,
        description="Был ли пользователь добавлен через invite-ссылку",
    )


class UpdateRoomMembership(BaseModel):
    is_active: bool | None = Field(
        default=None,
        description="Флаг активности membership",
    )


class RoomMembershipRead(BaseModel):
    id: int
    room_id: int
    user_id: int
    invite_id: int | None
    added_via_invite_link: bool
    is_active: bool
    joined_at: datetime
    created_at: datetime
    updated_at: datetime


class RoomMembershipListItem(BaseModel):
    id: int
    room_id: int
    user_id: int
    is_active: bool
    joined_at: datetime
