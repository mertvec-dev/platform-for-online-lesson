"""Сервис инвайт-токенов для преподавателей"""

import logging
from datetime import UTC, datetime
from secrets import token_urlsafe
from typing import cast

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .....models import TeacherInvite

logger = logging.getLogger(__name__)


class TeacherInviteService:
    async def create(
        self,
        created_by: int,
        max_uses: int | None,
        expires_at: datetime | None,
        session: AsyncSession,
    ) -> TeacherInvite:
        invite = TeacherInvite(
            token=token_urlsafe(32),
            created_by_user_id=created_by,
            max_uses=max_uses,
            expires_at=expires_at,
        )
        session.add(invite)
        await session.commit()
        logger.info("Создан инвайт-токен преподавателя: id=%d", invite.id)
        return invite

    async def list_all(self, session: AsyncSession) -> list[TeacherInvite]:
        stmt = select(TeacherInvite).order_by(TeacherInvite.created_at.desc())  # type: ignore[arg-type]
        result = await session.execute(stmt)
        return cast("list[TeacherInvite]", result.scalars().all())

    async def get_by_token(
        self, token: str, session: AsyncSession
    ) -> TeacherInvite | None:
        stmt = select(TeacherInvite).where(TeacherInvite.token == token)  # type: ignore[arg-type]
        result = await session.execute(stmt)
        return result.scalar()

    async def validate_and_consume(
        self, token: str, session: AsyncSession
    ) -> TeacherInvite:
        invite = await self.get_by_token(token, session)
        if invite is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Токен не найден"
            )

        if not invite.is_active:
            raise HTTPException(
                status_code=status.HTTP_410_GONE, detail="Токен деактивирован"
            )

        if invite.expires_at and invite.expires_at < datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_410_GONE, detail="Срок действия токена истёк"
            )

        if invite.max_uses and invite.used_count >= invite.max_uses:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Лимит использований токена исчерпан",
            )

        logger.info("Инвайт-токен преподавателя использован: id=%d", invite.id)
        return invite

    async def update(
        self,
        invite: TeacherInvite,
        is_active: bool | None,
        max_uses: int | None,
        expires_at: datetime | None,
        session: AsyncSession,
    ) -> TeacherInvite:
        if is_active is not None:
            invite.is_active = is_active
        if max_uses is not None:
            invite.max_uses = max_uses
        if expires_at is not None:
            invite.expires_at = expires_at
        await session.commit()
        logger.info("Обновлён инвайт-токен преподавателя: id=%d", invite.id)
        return invite

    async def delete(self, invite: TeacherInvite, session: AsyncSession) -> None:
        await session.delete(invite)
        await session.commit()
        logger.info("Удалён инвайт-токен преподавателя: id=%d", invite.id)


teacher_invite_service = TeacherInviteService()
