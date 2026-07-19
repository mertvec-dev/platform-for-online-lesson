"""Модель таблицы lessons"""

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, String
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .courses import Course
    from .lessons_logs import LessonLog


class LessonStatus(str, Enum):
    SCHEDULED = "scheduled"
    RUNNING = "running"
    ENDED = "ended"


class Lesson(SQLModel, table=True):
    __tablename__ = "lessons"  # type: ignore[attr-defined]

    __table_args__ = (
        CheckConstraint(
            "ended_at IS NULL OR started_at IS NULL OR ended_at >= started_at",
            name="ck_lessons_ended_after_started",
        ),
    )

    id: int = Field(
        default=None,
        primary_key=True,
    )

    course_id: int = Field(
        foreign_key="courses.id",
        index=True,
        ondelete="CASCADE",
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

    max_participants: int = Field(
        default=50,
        ge=1,
        le=50,
    )
    status: LessonStatus = Field(
        default=LessonStatus.SCHEDULED,
        index=True,
    )

    scheduled_at: datetime = Field(
        nullable=False,
        index=True,
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
    )

    started_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
    )
    ended_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
    )

    recording_url: str | None = Field(
        default=None,
        max_length=500,
        sa_type=String(500),
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

    # Отношения
    room: "Course" = Relationship(back_populates="lessons")

    # FK в дочерней таблице: ondelete="CASCADE" → только passive_deletes
    logs: list["LessonLog"] = Relationship(
        back_populates="lesson",
        passive_deletes=True,
    )
