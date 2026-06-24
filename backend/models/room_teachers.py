"""Модель дополнительных преподавателей комнаты"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .rooms import Room
    from .users import User


class RoomTeacher(SQLModel, table=True):
    __tablename__ = "room_teachers"  # type: ignore[attr-defined]

    __table_args__ = (
        UniqueConstraint("room_id", "user_id", name="uq_room_teachers_room_user"),
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
    added_by_user_id: int = Field(
        foreign_key="users.id",
        index=True,
        ondelete="CASCADE",
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

    room: "Room" = Relationship(
        back_populates="teachers",
    )  # Отношение многие к одному: много записей room_teacher --> одна комната

    teacher: "User" = Relationship(
        back_populates="teaching_assignments",
        sa_relationship_kwargs={"foreign_keys": "[RoomTeacher.user_id]"},
    )  # Отношение многие к одному: много назначений --> один преподаватель

    added_by: "User" = Relationship(
        back_populates="added_room_teachers",
        sa_relationship_kwargs={"foreign_keys": "[RoomTeacher.added_by_user_id]"},
    )  # Отношение многие к одному: много назначений --> один добавивший пользователь
