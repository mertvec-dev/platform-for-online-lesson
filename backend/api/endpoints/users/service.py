"""Сервис профилей"""

import logging
from typing import cast

from fastapi import HTTPException, status
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ....models import User
from ....models.users import Role

logger = logging.getLogger(__name__)


class UserService:
    async def get_user(
        self,
        user_id: int,
        session: AsyncSession,
    ) -> User:
        stmt = select(User).where(User.id == user_id)  # type: ignore[arg-type]

        result = await session.execute(stmt)
        user = result.scalar()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return user

    async def get_users(
        self,
        session: AsyncSession,
        limit: int = 100,
        offset: int = 0,
    ) -> list[User]:
        stmt = select(User).limit(limit).offset(offset)  # type: ignore[arg-type]
        result = await session.execute(stmt)
        users = result.scalars().all()
        return cast("list[User]", users)

    async def get_users_by_ids(
        self,
        users_ids: list[int],
        session: AsyncSession,
    ) -> list[User]:
        stmt = select(User).where(User.id.in_(users_ids))  # type: ignore[arg-type]
        result = await session.execute(stmt)
        users = result.scalars().all()
        return cast("list[User]", users)

    async def update_user(
        self,
        user: User,
        first_name: str | None,
        last_name: str | None,
        email: str | None,
        role: Role | None,
        is_active: bool | None,
        session: AsyncSession,
    ) -> User:
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if email is not None:
            user.email = email
        if role is not None:
            user.role = role
        if is_active is not None:
            user.is_active = is_active
        await session.commit()
        logger.info("Обновлён пользователь: id=%d", user.id)
        return user

    async def set_users_active(
        self,
        users_ids: list[int],
        is_active: bool,
        session: AsyncSession,
    ) -> None:
        stmt = update(User).where(User.id.in_(users_ids)).values(is_active=is_active)  # type: ignore[arg-type]
        await session.execute(stmt)
        await session.commit()
        logger.info(
            "Статус is_active=%s установлен для пользователей: user_ids=%s",
            is_active,
            users_ids,
        )

    async def delete_users(
        self,
        users_ids: list[int],
        session: AsyncSession,
    ) -> None:
        stmt = delete(User).where(User.id.in_(users_ids))  # type: ignore[arg-type]
        await session.execute(stmt)
        await session.commit()
        logger.info("Удалены пользователи: user_ids=%s", users_ids)


user_service = UserService()
