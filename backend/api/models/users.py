"""Модель для таблицы users"""

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .chat_messages import ChatMessage
    from .lessons_logs import LessonLog
    from .rooms import Room
    from .rooms_livekit_tokens import LivekitRoomToken


class Role(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore[attr-defined]

    id: int = Field(
        primary_key=True,
        index=True,
        sa_column_kwargs={"autoincrement": True},
    )

    first_name: str = Field()
    last_name: str = Field()
    password_hash: str = Field()

    email: str = Field(
        unique=True,
        index=True,
    )
    role: Role = Field(
        default=Role.STUDENT,
        index=True,
    )

    is_active: bool = Field(
        default=True,
        index=True,
    )

    deactivated_at: datetime | None = Field(
        default=None,
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    # Отношения
    rooms: list["Room"] = Relationship(
        back_populates="teacher",
    )  # Отношение один ко многим: один пользователь --> много комнат

    sent_messages: list["ChatMessage"] = Relationship(
        back_populates="author",
    )  # Отношение один ко многим: один пользователь --> много сообщений

    room_tokens: list["LivekitRoomToken"] = Relationship(
        back_populates="user",
        cascade_delete=True,
        passive_deletes=True,
    )  # Отношение один ко многим: один пользователь --> много токенов комнат

    lesson_logs: list["LessonLog"] = Relationship(
        back_populates="user",
    )  # Отношение один ко многим: один пользователь --> много логов уроков
