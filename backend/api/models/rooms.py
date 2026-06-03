"""Модель таблицы rooms"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .chat_messages import ChatMessage
    from .lessons import Lesson
    from .room_invites import RoomInvite
    from .room_memberships import RoomMembership
    from .room_teachers import RoomTeacher
    from .rooms_livekit_tokens import LivekitRoomToken
    from .users import User


class Room(SQLModel, table=True):
    __tablename__ = "rooms"  # type: ignore[attr-defined]

    id: int = Field(
        primary_key=True,
        index=True,
        sa_column_kwargs={"autoincrement": True},
    )

    created_by_user_id: int = Field(
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
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True,
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )
    is_active: bool = Field(
        default=True,
        index=True,
    )

    # Отношения
    created_by: "User" = Relationship(
        back_populates="created_rooms",
    )  # Отношение много к одному: много комнат --> один создатель

    messages: list["ChatMessage"] = Relationship(
        back_populates="room",
        cascade_delete=True,
        passive_deletes=True,
    )  # Отношение один к многим: одна комната --> много сообщений

    lessons: list["Lesson"] = Relationship(
        back_populates="room",
        cascade_delete=True,
        passive_deletes=True,
    )  # Отношение один к многим: одна комната --> много уроков

    tokens: list["LivekitRoomToken"] = Relationship(
        back_populates="room",
        cascade_delete=True,
        passive_deletes=True,
    )  # Отношение один к многим: одна комната --> много аудиторских записей токенов

    memberships: list["RoomMembership"] = Relationship(
        back_populates="room",
        cascade_delete=True,
        passive_deletes=True,
    )  # Отношение один к многим: одна комната --> много участников

    invites: list["RoomInvite"] = Relationship(
        back_populates="room",
        cascade_delete=True,
        passive_deletes=True,
    )  # Отношение один к многим: одна комната --> много invite-ссылок

    teachers: list["RoomTeacher"] = Relationship(
        back_populates="room",
        cascade_delete=True,
        passive_deletes=True,
    )  # Отношение один к многим: одна комната --> много назначений преподавателей
