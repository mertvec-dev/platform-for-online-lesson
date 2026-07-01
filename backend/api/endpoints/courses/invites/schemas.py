"""Схемы для пригласительных ссылок"""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateCourseInvite(BaseModel):
    max_uses: int | None = Field(
        default=None,
        gt=0,
        description="Максимальное число использований ссылки",
    )
    expires_at: datetime | None = Field(
        default=None,
        description="Время истечения ссылки",
    )


class UpdateCourseInvite(BaseModel):
    is_active: bool | None = Field(
        default=None,
        description="Флаг активности ссылки",
    )
    max_uses: int | None = Field(
        default=None,
        gt=0,
        description="Новое максимальное число использований",
    )
    expires_at: datetime | None = Field(
        default=None,
        description="Новое время истечения ссылки",
    )


class JoinCourseByInvite(BaseModel):
    token: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Токен пригласительной ссылки",
    )


class CourseInviteRead(BaseModel):
    id: int
    course_id: int
    created_by_user_id: int
    token: str
    is_active: bool
    max_uses: int | None
    used_count: int
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime
