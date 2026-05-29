"""Модель таблицы rooms_tokens, предназначенная для аудита токенов Livekit"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .rooms import Room
    from .users import User


class LivekitRoomToken(SQLModel, table=True):
    __tablename__ = "rooms_livekit_tokens"  # type: ignore[attr-defined]

    id: int = Field(
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

    joined_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    left_at: datetime | None = Field(
        default=None,
    )

    token: str = Field(
        unique=True,
        index=True,
        max_length=128,
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    expires_at: datetime | None = Field(
        default=None,
        index=True,
    )

    # Отношения
    room: "Room" = Relationship(
        back_populates="tokens"
    )  # Отношение многие к одному: много токенов --> одна комната

    user: "User" = Relationship(
        back_populates="room_tokens"
    )  # Отношение многие к одному: много токенов --> один пользователь
