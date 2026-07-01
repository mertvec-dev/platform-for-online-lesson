"""Сервис инвайт-ссылок"""

import logging
from datetime import datetime, timezone
from secrets import token_urlsafe

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .....models import CourseInvite, CourseMembership

logger = logging.getLogger(__name__)


class InviteRefCourseService:
    async def create_invite_ref(
        self,
        course_id: int,
        creator_id: int,
        max_uses: int | None,
        expires_at: datetime | None,
        session: AsyncSession,
    ) -> CourseInvite:
        invite_ref = CourseInvite(
            course_id=course_id,
            created_by_user_id=creator_id,
            token=token_urlsafe(32),
            max_uses=max_uses,
            expires_at=expires_at,
        )
        session.add(invite_ref)
        await session.commit()

        logger.info(
            "Создана инвайт-ссылка: id=%d, course_id=%d", invite_ref.id, course_id
        )
        return invite_ref

    async def get_invite_ref_by_course_id(
        self,
        course_id: int,
        session: AsyncSession,
    ) -> CourseInvite:
        stmt = select(CourseInvite).where(CourseInvite.course_id == course_id)  # type: ignore[arg-type]

        result = await session.execute(stmt)

        invite_ref = result.scalar()

        if invite_ref is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ссылка не найдена",
            )

        return invite_ref

    async def get_invite_ref(
        self,
        token: str,
        session: AsyncSession,
    ) -> CourseInvite:
        stmt = select(CourseInvite).where(CourseInvite.token == token)  # type: ignore[arg-type]

        result = await session.execute(stmt)
        invite_ref = result.scalar()

        if invite_ref is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ссылка не найдена. Проверьте ее на корректность.",
            )

        return invite_ref

    async def join_by_invites_ref(
        self,
        user_id: int,
        token: str,
        session: AsyncSession,
    ) -> None:
        invite_ref = await self.get_invite_ref(token, session)

        if not invite_ref.is_active:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Ссылка деактивирована.",
            )

        if invite_ref.expires_at and invite_ref.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Срок действия ссылки истёк.",
            )

        if invite_ref.max_uses and invite_ref.used_count >= invite_ref.max_uses:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Лимит использований исчерпан.",
            )

        stmt = select(CourseMembership).where(
            CourseMembership.course_id == invite_ref.course_id,  # type: ignore[arg-type]
            CourseMembership.user_id == user_id,  # type: ignore[arg-type]
        )
        result = await session.execute(stmt)

        existing_membership = result.scalar()

        if existing_membership is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Вы уже являетесь участником.",
            )

        membership = CourseMembership(
            course_id=invite_ref.course_id,
            user_id=user_id,
            invite_id=invite_ref.id,
            added_via_invite_link=True,
        )

        invite_ref.used_count += 1

        session.add(membership)
        await session.commit()

        logger.info(
            "Пользователь user_id=%d вступил в курс course_id=%d по инвайт-ссылке",
            user_id,
            invite_ref.course_id,
        )
        return None

    async def update_invite_ref(
        self,
        invite_ref: CourseInvite,
        is_active: bool | None,
        max_uses: int | None,
        expires_at: datetime | None,
        session: AsyncSession,
    ) -> None:
        if is_active is not None:
            invite_ref.is_active = is_active

        if max_uses is not None:
            invite_ref.max_uses = max_uses

        if expires_at is not None:
            invite_ref.expires_at = expires_at

        await session.commit()

        logger.info("Обновлена инвайт-ссылка: id=%d", invite_ref.id)
        return None

    async def delete_invite_ref(
        self,
        invite_ref: CourseInvite,
        session: AsyncSession,
    ) -> None:
        await session.delete(invite_ref)
        await session.commit()

        logger.info("Удалена инвайт-ссылка: id=%d", invite_ref.id)
        return None


invites_service = InviteRefCourseService()
