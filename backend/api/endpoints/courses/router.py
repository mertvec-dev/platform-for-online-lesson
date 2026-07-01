"""Роуты курсов"""

import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....models import Course, User
from ...core import db
from ...core.response import ApiResponse
from ..auth.dependencies import get_current_user
from .dependencies import (
    ensure_can_create_course,
    ensure_can_delete_course_by_slug,
    ensure_course_creator_or_admin_by_slug,
    ensure_course_member_or_admin_by_slug,
)
from .invites.router import invites_router
from .lessons.router import lesson_router
from .memberships.router import membership_router
from .schemas import CourseListItem, CourseRead, CreateCourse, UpdateCourse
from .service import course_service
from .teachers.router import teacher_router

course_router = APIRouter(
    prefix="/courses",
    tags=["courses"],
)

course_router.include_router(invites_router)
course_router.include_router(teacher_router)
course_router.include_router(membership_router)
course_router.include_router(lesson_router)

logger = logging.getLogger(__name__)


@course_router.post(
    "/create",
    summary="Создать курс",
    response_model=ApiResponse[CourseRead],
)
async def create_course(
    body: CreateCourse,
    current_user: User = Depends(ensure_can_create_course),
    session: AsyncSession = Depends(db.get_session),
):
    logger.info(
        "POST /courses/create — создание курса пользователем %d", current_user.id
    )
    course = await course_service.create_course(
        author_id=current_user.id,
        title=body.title,
        description=body.description,
        session=session,
    )

    return ApiResponse.ok(
        data=course,
        message="Курс создан",
        status_code=status.HTTP_201_CREATED,
    )


@course_router.get(
    "/my",
    summary="Мои курсы",
    response_model=ApiResponse[list[CourseListItem]],
)
async def get_my_courses(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    logger.info(
        "GET /courses/my — запрос списка курсов пользователя %d", current_user.id
    )
    courses = await course_service.list_user_courses(current_user.id, session)

    return ApiResponse.ok(
        data=courses,
        message="Список курсов",
        status_code=status.HTTP_200_OK,
    )


@course_router.get(
    "/{slug}",
    summary="Получить курс",
    response_model=ApiResponse[CourseRead],
)
async def get_course(
    course: Course = Depends(ensure_course_member_or_admin_by_slug),
):
    logger.info("GET /courses/%s — запрос курса", course.slug)
    return ApiResponse.ok(
        data=course,
        message="Курс найден",
        status_code=status.HTTP_200_OK,
    )


@course_router.patch(
    "/{slug}",
    summary="Обновить курс",
    response_model=ApiResponse[CourseRead],
)
async def update_course(
    body: UpdateCourse,
    course: Course = Depends(ensure_course_creator_or_admin_by_slug),
    session: AsyncSession = Depends(db.get_session),
):
    logger.info("PATCH /courses/%s — обновление курса", course.slug)
    course = await course_service.update_course(
        course,
        body.title,
        body.description,
        body.is_active,
        session,
    )

    return ApiResponse.ok(
        data=course,
        message="Курс обновлён",
        status_code=status.HTTP_200_OK,
    )


@course_router.delete(
    "/{slug}",
    summary="Удалить курс",
    response_model=ApiResponse[None],
)
async def delete_course(
    course: Course = Depends(ensure_can_delete_course_by_slug),
    session: AsyncSession = Depends(db.get_session),
):
    logger.info("DELETE /courses/%s — удаление курса", course.slug)
    await course_service.delete_course(course, session)
    return ApiResponse.ok(
        data=None,
        message="Курс удалён",
        status_code=status.HTTP_200_OK,
    )
