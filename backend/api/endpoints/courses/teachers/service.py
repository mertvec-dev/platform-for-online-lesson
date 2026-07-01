"""Сервисы для управления учителями"""

import logging
from typing import cast

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .....models import CourseTeacher

logger = logging.getLogger(__name__)


class TeacherService:
    async def add_teachers(
        self,
        course_id: int,
        user_ids: list[int],
        added_by_user_id: int,
        session: AsyncSession,
    ) -> list[CourseTeacher]:
        teachers = [
            CourseTeacher(
                course_id=course_id,
                user_id=uid,
                added_by_user_id=added_by_user_id,
            )
            for uid in user_ids
        ]
        session.add_all(teachers)
        await session.commit()
        logger.info(
            "Добавлены преподаватели в курс: course_id=%d, user_ids=%s",
            course_id,
            user_ids,
        )
        return teachers

    async def list_teachers(
        self,
        course_id: int,
        session: AsyncSession,
    ) -> list[CourseTeacher]:
        stmt = select(CourseTeacher).where(CourseTeacher.course_id == course_id)  # type: ignore[arg-type]
        result = await session.execute(stmt)
        return cast("list[CourseTeacher]", result.scalars().all())

    async def remove_teachers(
        self,
        course_id: int,
        user_ids: list[int],
        session: AsyncSession,
    ) -> None:
        stmt = select(CourseTeacher).where(
            CourseTeacher.course_id == course_id,  # type: ignore[arg-type]
            CourseTeacher.user_id.in_(user_ids),  # type: ignore[arg-type]
        )
        result = await session.execute(stmt)
        assignments = result.scalars().all()

        if not assignments:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Указанные преподаватели не найдены в курсе",
            )

        for assignment in assignments:
            await session.delete(assignment)
        await session.commit()
        logger.info(
            "Удалены преподаватели из курса: course_id=%d, user_ids=%s",
            course_id,
            user_ids,
        )


teacher_service = TeacherService()
