"""Зависимости и политики для уроков"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .....models import Course, Lesson, User
from .....models.users import Role
from ....core import db
from ....core.access_helpers import (
    _course_membership_exists,
    _course_teacher_assignment_exists,
    _get_course_of_lesson,
    get_lesson_or_404,
)
from ....core.permissions import Permission, RolePermissions
from ...auth.dependencies import get_current_user


class LessonAccessPolicy:
    """Правила доступа к урокам."""

    @staticmethod
    def can_view_lesson(
        user: User,
        course: Course,
        *,
        has_membership: bool,
    ) -> bool:
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.LESSON_VIEW):
            return False
        return course.created_by_user_id == user.id or has_membership

    @staticmethod
    def can_create_lesson(
        user: User,
        course: Course,
        *,
        is_course_teacher: bool,
    ) -> bool:
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.LESSON_CREATE):
            return False
        return course.created_by_user_id == user.id or is_course_teacher

    @staticmethod
    def can_update_lesson(
        user: User,
        course: Course,
        *,
        is_course_teacher: bool,
    ) -> bool:
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.LESSON_UPDATE):
            return False
        return course.created_by_user_id == user.id or is_course_teacher

    @staticmethod
    def can_delete_lesson(
        user: User,
        course: Course,
        *,
        is_course_teacher: bool,
    ) -> bool:
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.LESSON_DELETE):
            return False
        return course.created_by_user_id == user.id or is_course_teacher

    @staticmethod
    def can_start_lesson(
        user: User,
        course: Course,
        *,
        is_course_teacher: bool,
    ) -> bool:
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.LESSON_START):
            return False
        return course.created_by_user_id == user.id or is_course_teacher

    @staticmethod
    def can_end_lesson(
        user: User,
        course: Course,
        *,
        is_course_teacher: bool,
    ) -> bool:
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.LESSON_END):
            return False
        return course.created_by_user_id == user.id or is_course_teacher

    @staticmethod
    def can_view_lesson_logs(
        user: User,
        course: Course,
        *,
        is_course_teacher: bool,
    ) -> bool:
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.LESSON_VIEW_LOGS):
            return False
        return course.created_by_user_id == user.id or is_course_teacher


async def ensure_lesson_course_member_or_admin(
    lesson: Lesson = Depends(get_lesson_or_404),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(db.get_session),
) -> Lesson:
    """Разрешает доступ к уроку участнику его курса или администратору"""
    course = await _get_course_of_lesson(session, lesson)

    has_membership = await _course_membership_exists(
        session,
        lesson.course_id,
        current_user.id,
    )

    if LessonAccessPolicy.can_view_lesson(
        current_user, course, has_membership=has_membership
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
    """Разрешает управление уроком преподавателю курса, его создателю или администратору"""
    course = await _get_course_of_lesson(session, lesson)

    is_course_teacher = await _course_teacher_assignment_exists(
        session,
        lesson.course_id,
        current_user.id,
    )

    if LessonAccessPolicy.can_start_lesson(
        current_user,
        course,
        is_course_teacher=is_course_teacher,
    ):
        return lesson

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Пользователь не может управлять этим уроком",
    )
