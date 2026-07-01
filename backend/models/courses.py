"""Модель таблицы courses"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .chat_messages import ChatMessage
    from .course_invites import CourseInvite
    from .course_memberships import CourseMembership
    from .course_teachers import CourseTeacher
    from .courses_livekit_tokens import LivekitCourseToken
    from .lessons import Lesson
    from .users import User


class Course(SQLModel, table=True):
    __tablename__ = "courses"  # type: ignore[attr-defined]

    id: int = Field(
        default=None,
        primary_key=True,
    )

    created_by_user_id: int = Field(
        foreign_key="users.id",
        nullable=False,
        index=True,
        ondelete="RESTRICT",
    )

    title: str = Field(
        min_length=1,
        max_length=60,
        sa_type=String(60),  # type: ignore[arg-type]
    )
    description: str = Field(
        min_length=10,
        max_length=300,
        sa_type=String(300),  # type: ignore[arg-type]
    )

    slug: str = Field(
        min_length=1,
        max_length=72,
        unique=True,
        index=True,
        sa_type=String(72),  # type: ignore[arg-type]
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )
    is_active: bool = Field(default=True)

    # Отношения
    created_by: "User" = Relationship(back_populates="created_courses")

    # FK в дочерних таблицах имеют ondelete="CASCADE" → только passive_deletes
    messages: list["ChatMessage"] = Relationship(
        back_populates="room",
        passive_deletes=True,
    )

    lessons: list["Lesson"] = Relationship(
        back_populates="room",
        passive_deletes=True,
    )

    tokens: list["LivekitCourseToken"] = Relationship(
        back_populates="room",
        passive_deletes=True,
    )

    memberships: list["CourseMembership"] = Relationship(
        back_populates="room",
        passive_deletes=True,
    )

    invites: list["CourseInvite"] = Relationship(
        back_populates="room",
        passive_deletes=True,
    )

    teachers: list["CourseTeacher"] = Relationship(
        back_populates="room",
        passive_deletes=True,
    )
