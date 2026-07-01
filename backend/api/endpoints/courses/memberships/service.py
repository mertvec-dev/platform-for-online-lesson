"""Сервисы для управления участием"""

import logging
from typing import cast

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .....models import CourseMembership

logger = logging.getLogger(__name__)


class MembershipsService:
    async def list_members(
        self,
        course_id: int,
        session: AsyncSession,
    ) -> list[CourseMembership]:
        stmt = select(CourseMembership).where(CourseMembership.course_id == course_id)  # type: ignore[arg-type]
        result = await session.execute(stmt)

        return cast("list[CourseMembership]", result.scalars().all())

    async def remove_members(
        self,
        course_id: int,
        ids: list[int],
        session: AsyncSession,
    ) -> None:
        stmt = select(CourseMembership).where(
            CourseMembership.course_id == course_id,  # type: ignore[arg-type]
            CourseMembership.user_id.in_(ids),  # type: ignore[arg-type]
        )

        result = await session.execute(stmt)
        members = result.scalars().all()

        if not members:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Участники не найдены",
            )

        for member in members:
            await session.delete(member)

        await session.commit()

        logger.info(
            "Удалены участники из курса: course_id=%d, user_ids=%s", course_id, ids
        )
        return None


memberships_service = MembershipsService()
