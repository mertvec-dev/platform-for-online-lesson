"""Роуты для управления учителями"""

import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from .....models import Course, User
from ....core import ApiResponse, db
from ...auth.dependencies import get_current_user
from ..dependencies import ensure_course_creator_or_admin_by_slug
from .schemas import (
    AddCourseTeachers,
    CourseTeacherListItem,
    CourseTeacherRead,
    DeleteCourseTeachers,
)
from .service import teacher_service

teacher_router = APIRouter(tags=["course-teachers"])

logger = logging.getLogger(__name__)


@teacher_router.post(
    "/{slug}/teachers",
    summary="Добавить учителей",
    response_model=ApiResponse[list[CourseTeacherRead]],
)
async def add_teachers(
    body: AddCourseTeachers,
    course: Course = Depends(ensure_course_creator_or_admin_by_slug),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    logger.info(
        "POST /courses/%s/teachers — добавление учителей пользователем %d",
        course.slug,
        current_user.id,
    )
    teachers = await teacher_service.add_teachers(
        course_id=course.id,
        user_ids=body.user_ids,
        added_by_user_id=current_user.id,
        session=session,
    )
    return ApiResponse.ok(
        data=teachers,
        message="Учителя добавлены",
        status_code=status.HTTP_201_CREATED,
    )


@teacher_router.get(
    "/{slug}/teachers",
    summary="Получить список учителей",
    response_model=ApiResponse[list[CourseTeacherListItem]],
)
async def get_teachers(
    course: Course = Depends(ensure_course_creator_or_admin_by_slug),
    session: AsyncSession = Depends(db.get_session),
):
    logger.info("GET /courses/%s/teachers — запрос списка учителей", course.slug)
    teachers = await teacher_service.list_teachers(course.id, session)
    return ApiResponse.ok(data=teachers, message="Список учителей")


@teacher_router.delete(
    "/{slug}/teachers",
    summary="Удалить преподавателей из курса",
    response_model=ApiResponse[None],
)
async def delete_teachers(
    body: DeleteCourseTeachers,
    course: Course = Depends(ensure_course_creator_or_admin_by_slug),
    session: AsyncSession = Depends(db.get_session),
):
    logger.info("DELETE /courses/%s/teachers — удаление учителей", course.slug)
    await teacher_service.remove_teachers(
        course_id=course.id,
        user_ids=body.user_ids,
        session=session,
    )
    return ApiResponse.ok(data=None, message="Преподаватели удалены")
