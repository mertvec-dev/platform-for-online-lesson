"""Зависимости и политики для комнат"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....models import Room, User
from ....models.users import Role
from ...core import db
from ...core.access_helpers import (
    _room_membership_exists,
    _room_teacher_assignment_exists,
    get_room_or_404,
)
from ...core.permissions import Permission, RolePermissions
from ..auth.dependencies import get_current_user
from ..lessons.dependencies import LessonAccessPolicy


class RoomAccessPolicy:
    """Правила доступа к комнатам и их ресурсам."""

    @staticmethod
    def can_view_room(
        user: User,
        room: Room,
        *,
        has_membership: bool,
    ) -> bool:
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.ROOM_VIEW):
            return False
        return room.created_by_user_id == user.id or has_membership

    @staticmethod
    def can_create_room(user: User) -> bool:
        if user.role == Role.ADMIN:
            return True
        return RolePermissions.allows(user.role, Permission.ROOM_CREATE)

    @staticmethod
    def can_update_room(user: User, room: Room) -> bool:
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.ROOM_UPDATE):
            return False
        return room.created_by_user_id == user.id

    @staticmethod
    def can_delete_room(user: User, room: Room) -> bool:
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.ROOM_DELETE):
            return False
        return room.created_by_user_id == user.id

    @staticmethod
    def can_manage_room_teachers(user: User, room: Room) -> bool:
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.ROOM_MANAGE_TEACHERS):
            return False
        return room.created_by_user_id == user.id

    @staticmethod
    def can_manage_room_invites(user: User, room: Room) -> bool:
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.ROOM_MANAGE_INVITES):
            return False
        return room.created_by_user_id == user.id

    @staticmethod
    def can_view_room_members(
        user: User,
        room: Room,
        *,
        has_membership: bool,
    ) -> bool:
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.ROOM_VIEW_MEMBERS):
            return False
        return room.created_by_user_id == user.id or has_membership

    @staticmethod
    def can_remove_room_members(user: User, room: Room) -> bool:
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.ROOM_REMOVE_MEMBERS):
            return False
        return room.created_by_user_id == user.id

    @staticmethod
    def can_join_room(user: User) -> bool:
        if user.role == Role.ADMIN:
            return True
        return RolePermissions.allows(user.role, Permission.MEMBERSHIP_JOIN)

    @staticmethod
    def can_leave_room(
        user: User,
        *,
        has_membership: bool,
    ) -> bool:
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.MEMBERSHIP_LEAVE):
            return False
        return has_membership

    @staticmethod
    def can_join_by_invite(user: User) -> bool:
        if user.role == Role.ADMIN:
            return True
        return RolePermissions.allows(user.role, Permission.INVITE_JOIN)


async def ensure_can_create_room(
    current_user: User = Depends(get_current_user),
) -> User:
    if not RoomAccessPolicy.can_create_room(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для создания комнаты",
        )
    return current_user


async def ensure_room_creator_or_admin(
    room: Room = Depends(get_room_or_404),
    current_user: User = Depends(get_current_user),
) -> Room:
    if RoomAccessPolicy.can_update_room(current_user, room):
        return room
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Только создатель комнаты или администратор может выполнить это действие",
    )


async def ensure_can_delete_room(
    room: Room = Depends(get_room_or_404),
    current_user: User = Depends(get_current_user),
) -> Room:
    if RoomAccessPolicy.can_delete_room(current_user, room):
        return room
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Только администратор может удалить комнату",
    )


async def ensure_room_member_or_admin(
    room: Room = Depends(get_room_or_404),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(db.get_session),
) -> Room:
    assert current_user.id is not None
    assert room.id is not None
    has_membership = await _room_membership_exists(session, room.id, current_user.id)
    if RoomAccessPolicy.can_view_room(
        current_user, room, has_membership=has_membership
    ):
        return room
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Пользователь не состоит в этой комнате",
    )


async def ensure_room_teacher_or_admin(
    room: Room = Depends(get_room_or_404),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(db.get_session),
) -> Room:
    assert current_user.id is not None
    assert room.id is not None
    is_room_teacher = await _room_teacher_assignment_exists(
        session,
        room.id,
        current_user.id,
    )
    if LessonAccessPolicy.can_create_lesson(
        current_user,
        room,
        is_room_teacher=is_room_teacher,
    ):
        return room
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Пользователь не является преподавателем этой комнаты",
    )
