"""Модель для хранения логов занятий"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Index
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .lessons import Lesson
    from .users import User


class LessonLog(SQLModel, table=True):
    __tablename__ = "lessons_logs"  # type: ignore[attr-defined]

    __table_args__ = (
        Index("ix_lesson_logs_lesson_user_joined", "lesson_id", "user_id", "joined_at"),
    )

    id: int = Field(
        primary_key=True,
        sa_column_kwargs={"autoincrement": True},
    )
    lesson_id: int = Field(
        foreign_key="lessons.id",
        ondelete="CASCADE",
    )
    user_id: int = Field(
        foreign_key="users.id",
        index=True,
    )

    joined_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    left_at: datetime | None = Field(
        default=None,
    )

    duration_seconds: int | None = Field(
        default=None,
    )

    # Отношения
    lesson: "Lesson" = Relationship(
        back_populates="logs",
    )

    user: "User" = Relationship(
        back_populates="lesson_logs",
    )
