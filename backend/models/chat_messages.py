"""Модель таблицы chat_messages"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .courses import Course
    from .users import User


class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_messages"  # type: ignore[attr-defined]

    id: int = Field(
        default=None,
        primary_key=True,
    )

    course_id: int = Field(
        foreign_key="courses.id",
        index=True,
        ondelete="CASCADE",
    )

    author_id: int = Field(
        foreign_key="users.id",
        index=True,
        ondelete="RESTRICT",
    )

    text: str = Field(
        min_length=1,
        max_length=500,
        sa_type=String(500),  # type: ignore[arg-type]
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
        index=True,
    )

    # Отношения
    room: "Course" = Relationship(back_populates="messages")
    author: "User" = Relationship(back_populates="sent_messages")
