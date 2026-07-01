"""
Модель для хранения логов занятий (webhook-события LiveKit)

Таблица проектируется под массовую вставку: webhook-события от LiveKit
накапливаются и вставляются одним батчем в транзакции раз в N минут
или по окончании урока, чтобы не нагружать БД одиночными INSERT.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Index, String
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .lessons import Lesson
    from .users import User


class LessonLog(SQLModel, table=True):
    __tablename__ = "lessons_logs"  # type: ignore[attr-defined]

    __table_args__ = (
        Index(
            "ix_lesson_logs_open_session",
            "lesson_id",
            "user_id",
            postgresql_where="left_at IS NULL",
        ),
        Index(
            "ix_lesson_logs_lesson_user_joined",
            "lesson_id",
            "user_id",
            "joined_at",
        ),
        CheckConstraint(
            "left_at IS NULL OR left_at >= joined_at",
            name="ck_lesson_logs_left_after_joined",
        ),
        CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds >= 0",
            name="ck_lesson_logs_non_negative_duration",
        ),
    )

    id: int = Field(
        default=None,
        primary_key=True,
    )

    lesson_id: int = Field(
        foreign_key="lessons.id",
        index=True,
        ondelete="CASCADE",
    )
    user_id: int = Field(
        foreign_key="users.id",
        index=True,
        ondelete="RESTRICT",
    )

    # Идентификатор LiveKit-сессии (поле `id` из webhook-события).
    # Нужен для матчинга `participant_joined` ↔ `participant_left`
    # при ручной или отложенной обработке webhook-батчей.
    session_id: str | None = Field(
        default=None,
        max_length=255,
        index=True,
        sa_type=String(255),  # type: ignore[arg-type]
    )

    joined_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
    )
    left_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
    )
    duration_seconds: int | None = Field(default=None)

    # Временная метка получения webhook-события сервером.
    # Позволяет отследить задержку между реальным событием и его фиксацией.
    webhook_received_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
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
    lesson: "Lesson" = Relationship(back_populates="logs")
    user: "User" = Relationship(back_populates="lesson_logs")
