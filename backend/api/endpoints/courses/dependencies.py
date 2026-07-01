"""Зависимости и политики для курсов"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....models import Course, User
from ....models.users import Role
from ...core import db
from ...core.access_helpers import (
    _course_membership_exists,
    _course_teacher_assignment_exists,
    get_course_by_slug_or_404,
)
from ...core.permissions import Permission, RolePermissions
from ..auth.dependencies import get_current_user
from .lessons.dependencies import LessonAccessPolicy


class CourseAccessPolicy:
    """Правила доступа к курсам и их ресурсам."""

    @staticmethod
    def can_view_course(
        user: User,
        course: Course,
        *,
        has_membership: bool,
    ) -> bool:
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.COURSE_VIEW):
            return False
        return course.created_by_user_id == user.id or has_membership

    @staticmethod
    def can_create_course(user: User) -> bool:
        if user.role == Role.ADMIN:
            return True
        return RolePermissions.allows(user.role, Permission.COURSE_CREATE)

    @staticmethod
    def can_update_course(user: User, course: Course) -> bool:
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.COURSE_UPDATE):
            return False
        return course.created_by_user_id == user.id

    @staticmethod
    def can_delete_course(user: User, course: Course) -> bool:
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.COURSE_DELETE):
            return False
        return course.created_by_user_id == user.id

    @staticmethod
    def can_manage_course_teachers(user: User, course: Course) -> bool:
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.COURSE_MANAGE_TEACHERS):
            return False
        return course.created_by_user_id == user.id

    @staticmethod
    def can_manage_course_invites(user: User, course: Course) -> bool:
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.COURSE_MANAGE_INVITES):
            return False
        return course.created_by_user_id == user.id

    @staticmethod
    def can_view_course_members(
        user: User,
        course: Course,
        *,
        has_membership: bool,
    ) -> bool:
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.COURSE_VIEW_MEMBERS):
            return False
        return course.created_by_user_id == user.id or has_membership

    @staticmethod
    def can_remove_course_members(user: User, course: Course) -> bool:
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.COURSE_REMOVE_MEMBERS):
            return False
        return course.created_by_user_id == user.id

    @staticmethod
    def can_join_course(user: User) -> bool:
        if user.role == Role.ADMIN:
            return True
        return RolePermissions.allows(user.role, Permission.MEMBERSHIP_JOIN)

    @staticmethod
    def can_leave_course(
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


async def ensure_can_create_course(
    current_user: User = Depends(get_current_user),
) -> User:
    if not CourseAccessPolicy.can_create_course(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для создания курса",
        )
    return current_user


async def ensure_course_creator_or_admin_by_slug(
    course: Course = Depends(get_course_by_slug_or_404),
    current_user: User = Depends(get_current_user),
) -> Course:
    if CourseAccessPolicy.can_update_course(current_user, course):
        return course
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Только создатель курса или администратор может выполнить это действие",
    )


async def ensure_can_delete_course_by_slug(
    course: Course = Depends(get_course_by_slug_or_404),
    current_user: User = Depends(get_current_user),
) -> Course:
    if CourseAccessPolicy.can_delete_course(current_user, course):
        return course
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Только администратор может удалить курс",
    )


async def ensure_course_member_or_admin_by_slug(
    course: Course = Depends(get_course_by_slug_or_404),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(db.get_session),
) -> Course:
    has_membership = await _course_membership_exists(
        session, course.id, current_user.id
    )
    if CourseAccessPolicy.can_view_course(
        current_user, course, has_membership=has_membership
    ):
        return course
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Пользователь не состоит в этом курсе",
    )


async def ensure_course_teacher_or_admin_by_slug(
    course: Course = Depends(get_course_by_slug_or_404),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(db.get_session),
) -> Course:
    is_course_teacher = await _course_teacher_assignment_exists(
        session,
        course.id,
        current_user.id,
    )
    if LessonAccessPolicy.can_create_lesson(
        current_user,
        course,
        is_course_teacher=is_course_teacher,
    ):
        return course
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Пользователь не является преподавателем этого курса",
    )
