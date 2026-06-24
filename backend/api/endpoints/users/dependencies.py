"""Зависимости и политики для пользователей"""

from fastapi import Depends, HTTPException, status

from ..auth.dependencies import get_current_user
from ...core.permissions import Permission, RolePermissions
from ....models import User
from ....models.users import Role


class UserAccessPolicy:
    """Правила доступа к управлению пользователями."""

    @staticmethod
    def can_manage_roles(user: User) -> bool:
        if user.role == Role.ADMIN:
            return True
        return RolePermissions.allows(user.role, Permission.USER_MANAGE_ROLES)


async def ensure_can_manage_roles(
    current_user: User = Depends(get_current_user),
) -> User:
    """Разрешает управление ролями (только админ)."""
    if not UserAccessPolicy.can_manage_roles(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администратор может управлять ролями",
        )
    return current_user
