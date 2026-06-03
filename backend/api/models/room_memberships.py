"""Модель распределения пользователей по комнатам"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .room_invites import RoomInvite
    from .rooms import Room
    from .users import User


class RoomMembership(SQLModel, table=True):
    __tablename__ = "room_memberships"  # type: ignore[attr-defined]

    __table_args__ = (
        UniqueConstraint("room_id", "user_id", name="uq_room_memberships_room_user"),
    )

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
    invite_id: int | None = Field(
        default=None,
        foreign_key="room_invites.id",
        index=True,
        ondelete="SET NULL",
    )

    added_via_invite_link: bool = Field(
        default=False,
        index=True,
    )
    is_active: bool = Field(
        default=True,
        index=True,
    )

    joined_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
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
    room: "Room" = Relationship(
        back_populates="memberships",
    )  # Отношение многие к одному: много записей membership --> одна комната

    user: "User" = Relationship(
        back_populates="room_memberships",
    )  # Отношение многие к одному: много записей membership --> один пользователь

    invite: "RoomInvite | None" = Relationship(
        back_populates="memberships",
    )  # Отношение многие к одному: много вступлений могут ссылаться на одно приглашение
