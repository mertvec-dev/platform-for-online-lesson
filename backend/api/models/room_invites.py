"""Модель инвайт-ссылок для вступления в комнату"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .room_memberships import RoomMembership
    from .rooms import Room
    from .users import User


class RoomInvite(SQLModel, table=True):
    __tablename__ = "room_invites"  # type: ignore[attr-defined]

    __table_args__ = (
        CheckConstraint(
            "expires_at IS NULL OR expires_at >= created_at",
            name="ck_room_invites_expires_after_created",
        ),
        CheckConstraint(
            "max_uses IS NULL OR max_uses > 0",
            name="ck_room_invites_positive_max_uses",
        ),
        CheckConstraint(
            "used_count >= 0",
            name="ck_room_invites_non_negative_used_count",
        ),
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
    created_by_user_id: int = Field(
        foreign_key="users.id",
        index=True,
        ondelete="CASCADE",
    )

    token: str = Field(
        min_length=1,
        max_length=255,
        unique=True,
        index=True,
    )

    is_active: bool = Field(
        default=True,
        index=True,
    )
    max_uses: int | None = Field(
        default=None,
    )
    used_count: int = Field(
        default=0,
        index=True,
    )

    expires_at: datetime | None = Field(
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
    room: "Room" = Relationship(
        back_populates="invites",
    )  # Отношение многие к одному: много invite-ссылок --> одна комната

    created_by: "User" = Relationship(
        back_populates="created_room_invites",
    )  # Отношение многие к одному: много invite-ссылок --> один создатель

    memberships: list["RoomMembership"] = Relationship(
        back_populates="invite",
    )  # Отношение один к многим: одно приглашение --> много фактов вступления
