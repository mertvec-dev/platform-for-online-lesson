"""Модель таблицы chat_messages"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .rooms import Room
    from .users import User


class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_messages"  # type: ignore[attr-defined]

    id: int = Field(
        primary_key=True, index=True, sa_column_kwargs={"autoincrement": True}
    )

    room_id: int = Field(
        foreign_key="rooms.id",
        index=True,
        ondelete="CASCADE",
    )

    author_id: int = Field(
        foreign_key="users.id",
        index=True,
    )

    text: str = Field(
        max_length=500,
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True,
    )

    # Отношения
    room: "Room" = Relationship(
        back_populates="messages"
    )  # Отношение многое к одному: много сообщений --> одна комната
    author: "User" = Relationship(
        back_populates="sent_messages"
    )  # Отношение многое к одному: много пользователей --> одна комната
