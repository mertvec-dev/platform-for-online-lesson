"""Зависимости для role-based access control (RBAC)"""

from collections.abc import Awaitable, Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ....models import User
from ....models.users import Role
from ...core import db
from .jwt_tokens import get_current_user_id


async def get_current_user(
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(db.get_session),
) -> User:
    """Возвращает текущего пользователя из БД по `user_id` из JWT"""
    statement = select(User).where(User.id == current_user_id)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь из токена не найден",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь деактивирован",
        )

    return user


def require_roles(*allowed_roles: Role) -> Callable[..., Awaitable[User]]:
    """Создает зависимость, разрешающую доступ только указанным ролям"""
    allowed_roles_set = set(allowed_roles)

    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для выполнения действия",
            )

        return current_user

    return dependency


async def require_admin(
    current_user: User = Depends(require_roles(Role.ADMIN)),
) -> User:
    """Разрешает доступ только администраторам"""
    return current_user


async def require_teacher_or_admin(
    current_user: User = Depends(require_roles(Role.TEACHER, Role.ADMIN)),
) -> User:
    """Разрешает доступ преподавателям и администраторам"""
    return current_user
