"""Модель таблицы lessons"""

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .lessons_logs import LessonLog
    from .rooms import Room


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
        primary_key=True,
        sa_column_kwargs={"autoincrement": True},
    )

    room_id: int = Field(
        foreign_key="rooms.id",
        index=True,
        ondelete="CASCADE",
    )

    title: str = Field(
        min_length=1,
        max_length=60,
    )

    description: str = Field(
        min_length=10,
        max_length=300,
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

    # На какое время запланировано занятие
    scheduled_at: datetime = Field(
        nullable=False,
        index=True,
    )

    # Фактическое время начала занятия
    started_at: datetime | None = Field(
        default=None,
        index=True,
    )

    # Фактическое время завершения занятия
    ended_at: datetime | None = Field(
        default=None,
        index=True,
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True,
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )

    # Отношения
    room: "Room" = Relationship(
        back_populates="lessons"
    )  # Отношение многие к одному: много уроков --> одна комната

    logs: list["LessonLog"] = Relationship(
        back_populates="lesson",
        cascade_delete=True,
        passive_deletes=True,
    )  # Отношение один ко многим: один урок --> много логов
