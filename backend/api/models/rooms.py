"""Модель таблицы rooms"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .chat_messages import ChatMessage
    from .lessons import Lesson
    from .rooms_livekit_tokens import LivekitRoomToken
    from .users import User


class Room(SQLModel, table=True):
    __tablename__ = "rooms"  # type: ignore[attr-defined]

    id: int = Field(
        primary_key=True,
        index=True,
        sa_column_kwargs={"autoincrement": True},
    )

    teacher_id: int = Field(
        foreign_key="users.id",
        nullable=False,
        index=True,
    )

    title: str = Field(
        min_length=1,
        max_length=60,
    )
    description: str = Field(
        min_length=10,
        max_length=300,
    )

    slug: str = Field(
        min_length=1,
        max_length=64,
        unique=True,
        index=True,
    )

    max_participants: int = Field(
        default=50,
        ge=1,
        le=50,
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    started_at: datetime | None = Field(
        default=None,
    )
    ended_at: datetime | None = Field(
        default=None,
    )

    is_active: bool = Field(
        default=True,
        index=True,
    )

    # Отношения
    teacher: "User" = Relationship(
        back_populates="rooms"
    )  # Отношение много к одному: много комнат --> один преподаватель

    messages: list["ChatMessage"] = Relationship(
        back_populates="room",
        cascade_delete=True,
        passive_deletes=True,
    )  # Отношение один к многим: одна комната --> много сообщений

    lessons: list["Lesson"] = Relationship(
        back_populates="room",
        cascade_delete=True,
        passive_deletes=True,
    )  # Отношение одно к многим: одна комната --> много уроков

    tokens: list["LivekitRoomToken"] = Relationship(
        back_populates="room",
        cascade_delete=True,
        passive_deletes=True,
    )  # Отношение одно к многим: одна комната --> много токенов
