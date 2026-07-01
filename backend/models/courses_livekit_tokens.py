"""Модель таблицы аудита выдачи токенов LiveKit.

Хранит метаданные выданных LiveKit-токенов (не сами токены):
кто, в какой курс, когда получил доступ и когда срок истекает.

Также рассчитана на батч-вставку: при старте урока токены генерируются
для всех участников и вставляются одним INSERT.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Index, String
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .courses import Course
    from .users import User


class LivekitCourseToken(SQLModel, table=True):
    __tablename__ = "courses_livekit_tokens"  # type: ignore[attr-defined]

    __table_args__ = (
        Index(
            "ix_room_tokens_course_user_joined",
            "course_id",
            "user_id",
            "joined_at",
        ),
        CheckConstraint(
            "left_at IS NULL OR left_at >= joined_at",
            name="ck_room_tokens_left_after_joined",
        ),
        CheckConstraint(
            "expires_at IS NULL OR expires_at >= created_at",
            name="ck_room_tokens_expires_after_created",
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
    user_id: int = Field(
        foreign_key="users.id",
        index=True,
        ondelete="CASCADE",
    )

    participant_identity: str = Field(
        min_length=1,
        max_length=255,
        sa_type=String(255),  # type: ignore[arg-type]
    )
    token_jti: str | None = Field(
        default=None,
        unique=True,
        index=True,
        min_length=1,
        max_length=255,
        sa_type=String(255),  # type: ignore[arg-type]
    )

    # Идентификатор LiveKit-сессии — позволяет связать запись токена
    # с конкретным уроком/подключением при отладке.
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

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )
    expires_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
    )

    # Отношения
    room: "Course" = Relationship(back_populates="tokens")
    user: "User" = Relationship(back_populates="room_tokens")
