"""Схемы для участников курса"""

from datetime import datetime

from pydantic import BaseModel, Field


class UpdateCourseMembership(BaseModel):
    is_active: bool | None = Field(
        default=None,
        description="Флаг активности membership",
    )


class RemoveMembers(BaseModel):
    user_ids: list[int] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Идентификаторы участников",
    )


class CourseMembershipRead(BaseModel):
    id: int
    course_id: int
    user_id: int
    invite_id: int | None
    added_via_invite_link: bool
    is_active: bool
    joined_at: datetime
    created_at: datetime
    updated_at: datetime


class CourseMembershipListItem(BaseModel):
    id: int
    course_id: int
    user_id: int
    is_active: bool
    joined_at: datetime
