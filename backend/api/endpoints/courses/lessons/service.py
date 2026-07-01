"""Сервис для уроков"""

import logging
from datetime import datetime, timezone
from typing import cast

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .....models import Lesson
from .....models.lessons import LessonStatus
from ....core.pagination import MAX_PAGE_SIZE

logger = logging.getLogger(__name__)


class LessonService:
    async def create_lesson(
        self,
        course_id: int,
        title: str,
        description: str,
        max_participants: int,
        scheduled_at: datetime,
        session: AsyncSession,
    ) -> Lesson:
        lesson = Lesson(
            course_id=course_id,
            title=title,
            description=description,
            max_participants=max_participants,
            scheduled_at=scheduled_at,
        )
        session.add(lesson)
        await session.commit()
        logger.info(
            "Создан урок: id=%d, course_id=%d, title=%s", lesson.id, course_id, title
        )
        return lesson

    async def get_lesson(
        self,
        lesson_id: int,
        session: AsyncSession,
    ) -> Lesson | None:
        return await session.get(Lesson, lesson_id)

    async def get_lessons(
        self,
        course_id: int,
        session: AsyncSession,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Lesson]:
        stmt = (
            select(Lesson)
            .where(Lesson.course_id == course_id)  # type: ignore[arg-type]
            .order_by(Lesson.scheduled_at.desc())  # type: ignore
            .limit(min(limit, MAX_PAGE_SIZE))
            .offset(offset)
        )
        result = await session.execute(stmt)
        return cast("list[Lesson]", result.scalars().all())

    async def update_lesson(
        self,
        lesson: Lesson,
        title: str | None,
        description: str | None,
        max_participants: int | None,
        scheduled_at: datetime | None,
        session: AsyncSession,
    ) -> Lesson:
        if title is not None:
            lesson.title = title
        if description is not None:
            lesson.description = description
        if max_participants is not None:
            lesson.max_participants = max_participants
        if scheduled_at is not None:
            lesson.scheduled_at = scheduled_at

        await session.commit()
        logger.info("Обновлён урок: id=%d", lesson.id)
        return lesson

    async def start_lesson(
        self,
        lesson: Lesson,
        started_at: datetime | None,
        session: AsyncSession,
    ) -> Lesson:
        if lesson.status != LessonStatus.SCHEDULED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Можно начать только запланированный урок",
            )

        lesson.status = LessonStatus.RUNNING
        lesson.started_at = started_at or datetime.now(timezone.utc)
        await session.commit()
        logger.info("Урок начат: id=%d", lesson.id)
        return lesson

    async def end_lesson(
        self,
        lesson: Lesson,
        ended_at: datetime | None,
        session: AsyncSession,
    ) -> Lesson:
        if lesson.status != LessonStatus.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Можно завершить только идущий урок",
            )

        lesson.status = LessonStatus.ENDED
        lesson.ended_at = ended_at or datetime.now(timezone.utc)
        await session.commit()
        logger.info("Урок завершён: id=%d", lesson.id)
        return lesson

    async def delete_lesson(
        self,
        lesson: Lesson,
        session: AsyncSession,
    ) -> None:
        await session.delete(lesson)
        await session.commit()
        logger.info("Удалён урок: id=%d", lesson.id)


lesson_service = LessonService()
