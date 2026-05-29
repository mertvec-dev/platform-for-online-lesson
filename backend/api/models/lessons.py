"""Модель таблицы lessons"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .lessons_logs import LessonLog
    from .rooms import Room


class Lesson(SQLModel, table=True):
    __tablename__ = "lessons"  # type: ignore[attr-defined]

    id: int = Field(
        primary_key=True,
        sa_column_kwargs={"autoincrement": True},
    )

    room_id: int = Field(
        foreign_key="rooms.id",
        index=True,
        ondelete="CASCADE",
    )

    title: str = Field(
        min_length=1,
        max_length=60,
    )

    description: str = Field(
        min_length=10,
        max_length=300,
    )

    scheduled_at: datetime = Field(
        nullable=False,
        index=True,
        default_factory=lambda: datetime.now(timezone.utc),
    )

    # Отношения
    room: "Room" = Relationship(
        back_populates="lessons"
    )  # Отношение один к одному: один урок --> одна комната

    logs: list["LessonLog"] = Relationship(
        back_populates="lesson",
        cascade_delete=True,
        passive_deletes=True,
    )  # Отношение один ко многим: один урок --> много логов
