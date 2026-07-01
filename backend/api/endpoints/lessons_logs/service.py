"""Сервис для логов посещения уроков."""

import logging
import re
from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.lessons_logs import LessonLog

logger = logging.getLogger(__name__)

# Извлекает ID курса и урока из названия комнаты.
# Ожидаемый формат: "course_123_lesson_456"
# Возвращает: group(1) = course_id, group(2) = lesson_id
_ROOM_NAME_RE = re.compile(r"^course_(\d+)_lesson_(\d+)$")


def parse_room_name(room_name: str) -> tuple[int, int] | None:
    m = _ROOM_NAME_RE.match(room_name)
    if m is None:
        return None
    return int(m.group(1)), int(m.group(2))


class LessonLogService:
    async def get_logs_for_lesson(
        self,
        lesson_id: int,
        session: AsyncSession,
    ) -> list[LessonLog]:
        stmt = (
            select(LessonLog)
            .where(LessonLog.lesson_id == lesson_id)
            .order_by(LessonLog.joined_at.asc())
        )
        result = await session.execute(stmt)
        return cast("list[LessonLog]", result.scalars().all())

    async def get_logs_for_user_in_lesson(
        self,
        lesson_id: int,
        user_id: int,
        session: AsyncSession,
    ) -> list[LessonLog]:
        stmt = (
            select(LessonLog)
            .where(
                LessonLog.lesson_id == lesson_id,
                LessonLog.user_id == user_id,
            )
            .order_by(LessonLog.joined_at.asc())
        )
        result = await session.execute(stmt)
        return cast("list[LessonLog]", result.scalars().all())


lesson_log_service = LessonLogService()
