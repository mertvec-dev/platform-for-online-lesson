"""Модель таблицы аудита выдачи токенов LiveKit"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .rooms import Room
    from .users import User


class LivekitRoomToken(SQLModel, table=True):
    __tablename__ = "rooms_livekit_tokens"  # type: ignore[attr-defined]

    __table_args__ = (
        CheckConstraint(
            "left_at IS NULL OR left_at >= joined_at",
            name="ck_room_tokens_left_after_joined",
        ),
        CheckConstraint(
            "expires_at IS NULL OR expires_at >= created_at",
            name="ck_room_tokens_expires_after_created",
        ),
    )

    id: int | None = Field(
        default=None,
        primary_key=True,
        index=True,
        sa_column_kwargs={"autoincrement": True},
    )

    room_id: int = Field(
        foreign_key="rooms.id",
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
        index=True,
    )
    token_jti: str | None = Field(
        default=None,
        unique=True,
        index=True,
        min_length=1,
        max_length=255,
    )

    joined_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True,
    )
    left_at: datetime | None = Field(
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
    expires_at: datetime | None = Field(
        default=None,
        index=True,
    )

    # Отношения
    room: "Room" = Relationship(
        back_populates="tokens"
    )  # Отношение многие к одному: много аудиторских записей токенов --> одна комната

    user: "User" = Relationship(
        back_populates="room_tokens"
    )  # Отношение многие к одному: много аудиторских записей токенов --> один пользователь
