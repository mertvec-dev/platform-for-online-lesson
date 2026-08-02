"""Модель инвайт-ссылок для вступления в комнату"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, String
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .course_memberships import CourseMembership
    from .courses import Course
    from .users import User


class CourseInvite(SQLModel, table=True):
    __tablename__ = "course_invites"  # type: ignore[attr-defined]

    __table_args__ = (
        CheckConstraint(
            "expires_at IS NULL OR expires_at >= created_at",
            name="ck_course_invites_expires_after_created",
        ),
        CheckConstraint(
            "max_uses IS NULL OR max_uses > 0",
            name="ck_course_invites_positive_max_uses",
        ),
        CheckConstraint(
            "used_count >= 0",
            name="ck_course_invites_non_negative_used_count",
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
        sa_type=String(255),  # type: ignore[arg-type]
    )

    is_active: bool = Field(default=True)
    max_uses: int | None = Field(default=None)
    used_count: int = Field(default=0)

    expires_at: datetime | None = Field(
        default=None,
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
    room: "Course" = Relationship(back_populates="invites")
    created_by: "User" = Relationship(back_populates="created_course_invites")
    memberships: list["CourseMembership"] = Relationship(back_populates="invite")
