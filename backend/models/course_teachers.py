"""Модель дополнительных преподавателей курса"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .courses import Course
    from .users import User


class CourseTeacher(SQLModel, table=True):
    __tablename__ = "course_teachers"  # type: ignore[attr-defined]

    __table_args__ = (
        UniqueConstraint("course_id", "user_id", name="uq_course_teachers_room_user"),
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
    added_by_user_id: int | None = Field(
        default=None,
        foreign_key="users.id",
        index=True,
        ondelete="SET NULL",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )

    # Отношения
    room: "Course" = Relationship(back_populates="teachers")

    teacher: "User" = Relationship(
        back_populates="teaching_assignments",
        sa_relationship_kwargs={"foreign_keys": "[CourseTeacher.user_id]"},
    )

    added_by: "User" = Relationship(
        back_populates="added_course_teachers",
        sa_relationship_kwargs={"foreign_keys": "[CourseTeacher.added_by_user_id]"},
    )
