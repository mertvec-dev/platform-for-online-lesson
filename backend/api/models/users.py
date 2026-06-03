"""Модель для таблицы users"""

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .chat_messages import ChatMessage
    from .lessons_logs import LessonLog
    from .room_invites import RoomInvite
    from .room_memberships import RoomMembership
    from .room_teachers import RoomTeacher
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

    first_name: str = Field(
        min_length=1,
        max_length=100,
    )
    last_name: str = Field(
        min_length=1,
        max_length=100,
    )
    password_hash: str = Field(
        min_length=1,
        max_length=255,
    )

    email: str = Field(
        min_length=3,
        max_length=255,
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

    # Отношения
    created_rooms: list["Room"] = Relationship(
        back_populates="created_by",
    )  # Отношение один ко многим: один пользователь --> много созданных комнат

    sent_messages: list["ChatMessage"] = Relationship(
        back_populates="author",
    )  # Отношение один ко многим: один пользователь --> много сообщений

    room_tokens: list["LivekitRoomToken"] = Relationship(
        back_populates="user",
        cascade_delete=True,
        passive_deletes=True,
    )  # Отношение один ко многим: один пользователь --> много аудиторских записей токенов комнат

    lesson_logs: list["LessonLog"] = Relationship(
        back_populates="user",
    )  # Отношение один ко многим: один пользователь --> много логов уроков

    room_memberships: list["RoomMembership"] = Relationship(
        back_populates="user",
        cascade_delete=True,
        passive_deletes=True,
    )  # Отношение один ко многим: один пользователь --> много membership-записей комнат

    created_room_invites: list["RoomInvite"] = Relationship(
        back_populates="created_by",
        cascade_delete=True,
        passive_deletes=True,
    )  # Отношение один ко многим: один пользователь --> много созданных invite-ссылок

    teaching_assignments: list["RoomTeacher"] = Relationship(
        back_populates="teacher",
        cascade_delete=True,
        passive_deletes=True,
        sa_relationship_kwargs={"foreign_keys": "[RoomTeacher.user_id]"},
    )  # Отношение один ко многим: один пользователь --> много назначений преподавателем

    added_room_teachers: list["RoomTeacher"] = Relationship(
        back_populates="added_by",
        cascade_delete=True,
        passive_deletes=True,
        sa_relationship_kwargs={"foreign_keys": "[RoomTeacher.added_by_user_id]"},
    )  # Отношение один ко многим: один пользователь --> много добавлений преподавателей в комнаты
