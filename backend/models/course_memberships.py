"""Модель распределения пользователей по курсам"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .course_invites import CourseInvite
    from .courses import Course
    from .users import User


class CourseMembership(SQLModel, table=True):
    __tablename__ = "course_memberships"  # type: ignore[attr-defined]

    __table_args__ = (
        UniqueConstraint(
            "course_id", "user_id", name="uq_course_memberships_room_user"
        ),
    )

    id: int = Field(
        default=None,
        primary_key=True,
    )

    course_id: int = Field(
        foreign_key="courses.id",
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
        foreign_key="course_invites.id",
        index=True,
        ondelete="SET NULL",
    )

    added_via_invite_link: bool = Field(default=False)
    is_active: bool = Field(default=True)

    joined_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )

    # Отношения
    room: "Course" = Relationship(back_populates="memberships")
    user: "User" = Relationship(back_populates="course_memberships")
    invite: "CourseInvite" = Relationship(back_populates="memberships")
