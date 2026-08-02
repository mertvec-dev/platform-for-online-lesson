"""Модель для таблицы users"""

from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .chat_messages import ChatMessage
    from .course_invites import CourseInvite
    from .course_memberships import CourseMembership
    from .course_teachers import CourseTeacher
    from .courses import Course
    from .courses_livekit_tokens import LivekitCourseToken
    from .lessons_logs import LessonLog


class Role(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore[attr-defined]

    id: int = Field(
        default=None,
        primary_key=True,
    )

    first_name: str = Field(
        min_length=1,
        max_length=100,
        sa_type=String(100),  # type: ignore[arg-type]
    )
    last_name: str = Field(
        min_length=1,
        max_length=100,
        sa_type=String(100),  # type: ignore[arg-type]
    )
    password_hash: str = Field(
        max_length=255,
        sa_type=String(255),  # type: ignore[arg-type]
    )

    email: str = Field(
        min_length=3,
        max_length=255,
        unique=True,
        index=True,
        nullable=False,
        sa_type=String(255),  # type: ignore[arg-type]
    )
    role: Role = Field(
        default=Role.STUDENT,
        index=True,
    )

    is_active: bool = Field(
        default=True,
        index=True,
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )

    # Отношения
    created_courses: list["Course"] = Relationship(back_populates="created_by")

    sent_messages: list["ChatMessage"] = Relationship(back_populates="author")

    room_tokens: list["LivekitCourseToken"] = Relationship(
        back_populates="user",
        passive_deletes=True,
    )

    lesson_logs: list["LessonLog"] = Relationship(back_populates="user")

    course_memberships: list["CourseMembership"] = Relationship(
        back_populates="user",
        passive_deletes=True,
    )

    created_course_invites: list["CourseInvite"] = Relationship(
        back_populates="created_by",
        passive_deletes=True,
    )

    teaching_assignments: list["CourseTeacher"] = Relationship(
        back_populates="teacher",
        passive_deletes=True,
        sa_relationship_kwargs={"foreign_keys": "[CourseTeacher.user_id]"},
    )

    added_course_teachers: list["CourseTeacher"] = Relationship(
        back_populates="added_by",
        passive_deletes=True,
        sa_relationship_kwargs={"foreign_keys": "[CourseTeacher.added_by_user_id]"},
    )
