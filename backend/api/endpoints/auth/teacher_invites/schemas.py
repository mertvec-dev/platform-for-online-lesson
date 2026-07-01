"""Схемы для инвайт-токенов преподавателей"""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateTeacherInvite(BaseModel):
    max_uses: int | None = Field(
        default=None,
        gt=0,
        description="Максимальное число использований",
    )
    expires_at: datetime | None = Field(
        default=None,
        description="Дата истечения",
    )


class UpdateTeacherInvite(BaseModel):
    is_active: bool | None = Field(default=None)
    max_uses: int | None = Field(default=None, gt=0)
    expires_at: datetime | None = Field(default=None)


class TeacherInviteRead(BaseModel):
    id: int
    token: str
    created_by_user_id: int | None
    is_active: bool
    max_uses: int | None
    used_count: int
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TeacherInviteListItem(BaseModel):
    id: int
    token: str
    is_active: bool
    used_count: int
    max_uses: int | None
    expires_at: datetime | None
