"""Сервис курсов"""

import logging
import secrets
from typing import cast

from slugify import slugify
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from ....models import Course, CourseMembership

logger = logging.getLogger(__name__)

MAX_SLUG = 72
SUFFIX_LEN = 5  # дефис + 4-hex символа


class CoursesService:
    def _make_slug(self, title: str) -> str:
        raw = slugify(title) or "course"
        return raw[: MAX_SLUG - SUFFIX_LEN].rstrip("-")

    async def _unique_slug(self, title: str, session: AsyncSession) -> str:
        base = self._make_slug(title)
        while True:
            candidate = f"{base}-{secrets.token_hex(2)}"

            stmt = select(exists(1)).where(Course.slug == candidate)  # type: ignore[arg-type]
            result = await session.execute(stmt)

            if not result.scalar():
                return candidate

    async def create_course(
        self,
        author_id: int,
        title: str,
        description: str,
        session: AsyncSession,
    ) -> Course:
        slug = await self._unique_slug(title, session)
        course = Course(
            created_by_user_id=author_id,
            title=title,
            description=description,
            slug=slug,
        )
        session.add(course)
        await session.flush()

        membership = CourseMembership(
            course_id=course.id,
            user_id=author_id,
            is_active=True,
        )
        session.add(membership)
        await session.commit()

        logger.info(
            "Создан курс: id=%d, title=%s, author_id=%d", course.id, title, author_id
        )
        return course

    async def update_course(
        self,
        course: Course,
        title: str | None,
        description: str | None,
        is_active: bool | None,
        session: AsyncSession,
    ) -> Course:
        if title is not None and course.title != title:
            course.title = title
            course.slug = await self._unique_slug(title, session)

        if description is not None:
            course.description = description

        if is_active is not None:
            course.is_active = is_active

        await session.commit()

        logger.info("Обновлён курс: id=%d", course.id)
        return course

    async def list_user_courses(
        self,
        user_id: int,
        session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Course]:
        stmt = (
            select(Course)
            .join(CourseMembership, CourseMembership.course_id == Course.id)  # type: ignore[arg-type]
            .where(CourseMembership.user_id == user_id)  # type: ignore[arg-type]
            .order_by(Course.created_at.desc())  # type: ignore
            .limit(limit)
            .offset(offset)
        )

        result = await session.execute(stmt)
        courses = result.scalars().all()

        return cast("list[Course]", courses)

    async def delete_course(
        self,
        course: Course,
        session: AsyncSession,
    ) -> None:
        await session.delete(course)
        await session.commit()
        logger.info("Удалён курс: id=%d, title=%s", course.id, course.title)


course_service = CoursesService()
