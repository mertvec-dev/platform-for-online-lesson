"""Зависимости и политики для уроков"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import get_current_user
from ...core import db
from ...core.access_helpers import (
    _get_room_of_lesson,
    _room_membership_exists,
    _room_teacher_assignment_exists,
    get_lesson_or_404,
)
from ...core.permissions import Permission, RolePermissions
from ....models import Lesson, Room, User
from ....models.users import Role


class LessonAccessPolicy:
    """Правила доступа к урокам."""

    @staticmethod
    def can_view_lesson(
        user: User,
        room: Room,
        *,
        has_membership: bool,
    ) -> bool:
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.LESSON_VIEW):
            return False
        return room.created_by_user_id == user.id or has_membership

    @staticmethod
    def can_create_lesson(
        user: User,
        room: Room,
        *,
        is_room_teacher: bool,
    ) -> bool:
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.LESSON_CREATE):
            return False
        return room.created_by_user_id == user.id or is_room_teacher

    @staticmethod
    def can_update_lesson(
        user: User,
        room: Room,
        *,
        is_room_teacher: bool,
    ) -> bool:
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.LESSON_UPDATE):
            return False
        return room.created_by_user_id == user.id or is_room_teacher

    @staticmethod
    def can_delete_lesson(
        user: User,
        room: Room,
        *,
        is_room_teacher: bool,
    ) -> bool:
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.LESSON_DELETE):
            return False
        return room.created_by_user_id == user.id or is_room_teacher

    @staticmethod
    def can_start_lesson(
        user: User,
        room: Room,
        *,
        is_room_teacher: bool,
    ) -> bool:
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.LESSON_START):
            return False
        return room.created_by_user_id == user.id or is_room_teacher

    @staticmethod
    def can_end_lesson(
        user: User,
        room: Room,
        *,
        is_room_teacher: bool,
    ) -> bool:
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.LESSON_END):
            return False
        return room.created_by_user_id == user.id or is_room_teacher

    @staticmethod
    def can_view_lesson_logs(
        user: User,
        room: Room,
        *,
        is_room_teacher: bool,
    ) -> bool:
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.LESSON_VIEW_LOGS):
            return False
        return room.created_by_user_id == user.id or is_room_teacher


async def ensure_lesson_room_member_or_admin(
    lesson: Lesson = Depends(get_lesson_or_404),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(db.get_session),
) -> Lesson:
    """Разрешает доступ к уроку участнику его комнаты или администратору"""
    room = await _get_room_of_lesson(session, lesson)

    assert current_user.id is not None
    has_membership = await _room_membership_exists(
        session,
        lesson.room_id,
        current_user.id,
    )

    if LessonAccessPolicy.can_view_lesson(
        current_user, room, has_membership=has_membership
    ):
        return lesson

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Пользователь не имеет доступа к этому уроку",
    )


async def ensure_lesson_teacher_or_admin(
    lesson: Lesson = Depends(get_lesson_or_404),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(db.get_session),
) -> Lesson:
    """Разрешает управление уроком преподавателю комнаты, её создателю или администратору"""
    room = await _get_room_of_lesson(session, lesson)

    assert current_user.id is not None
    is_room_teacher = await _room_teacher_assignment_exists(
        session,
        lesson.room_id,
        current_user.id,
    )

    if LessonAccessPolicy.can_start_lesson(
        current_user,
        room,
        is_room_teacher=is_room_teacher,
    ):
        return lesson

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Пользователь не может управлять этим уроком",
    )
