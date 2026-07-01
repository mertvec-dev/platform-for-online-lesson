"""Роуты для управление инвайт-ссылками"""

import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from .....models import Course, User
from ....core import ApiResponse, db
from ...auth.dependencies import get_current_user
from ..dependencies import ensure_course_creator_or_admin_by_slug
from .schemas import CourseInviteRead, CreateCourseInvite, UpdateCourseInvite
from .service import invites_service

invites_router = APIRouter(tags=["courses-invites"])

logger = logging.getLogger(__name__)


@invites_router.get(
    "/{slug}/invite",
    summary="Получить инвайт-ссылку курса",
    response_model=ApiResponse[CourseInviteRead],
)
async def get_invite_ref(
    course: Course = Depends(ensure_course_creator_or_admin_by_slug),
    session: AsyncSession = Depends(db.get_session),
):
    logger.info("GET /courses/%s/invite — запрос инвайт-ссылки курса", course.slug)
    invite = await invites_service.get_invite_ref_by_course_id(course.id, session)
    return ApiResponse.ok(
        data=invite,
        message="Ссылка курса",
        status_code=status.HTTP_200_OK,
    )


@invites_router.post(
    "/{slug}/invite",
    summary="Создать инвайт-ссылку",
    response_model=ApiResponse[CourseInviteRead],
)
async def create_invite_ref(
    body: CreateCourseInvite,
    course: Course = Depends(ensure_course_creator_or_admin_by_slug),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    logger.info(
        "POST /courses/%s/invite — создание инвайт-ссылки пользователем %d",
        course.slug,
        current_user.id,
    )
    invite = await invites_service.create_invite_ref(
        course_id=course.id,
        creator_id=current_user.id,
        max_uses=body.max_uses,
        expires_at=body.expires_at,
        session=session,
    )
    return ApiResponse.ok(
        data=invite,
        message="Ссылка создана",
        status_code=status.HTTP_201_CREATED,
    )


@invites_router.patch(
    "/{slug}/invite",
    summary="Обновить параметры ссылки",
    response_model=ApiResponse[None],
)
async def edit_invite_ref(
    body: UpdateCourseInvite,
    course: Course = Depends(ensure_course_creator_or_admin_by_slug),
    session: AsyncSession = Depends(db.get_session),
):
    logger.info("PATCH /courses/%s/invite — обновление инвайт-ссылки", course.slug)
    invite_ref = await invites_service.get_invite_ref_by_course_id(course.id, session)

    await invites_service.update_invite_ref(
        invite_ref=invite_ref,
        is_active=body.is_active,
        max_uses=body.max_uses,
        expires_at=body.expires_at,
        session=session,
    )
    return ApiResponse.ok(
        data=None,
        message="Параметры ссылки обновлены",
        status_code=status.HTTP_200_OK,
    )


@invites_router.delete(
    "/{slug}/invite",
    summary="Удалить ссылку",
    response_model=ApiResponse[None],
)
async def delete_invite_ref(
    course: Course = Depends(ensure_course_creator_or_admin_by_slug),
    session: AsyncSession = Depends(db.get_session),
):
    logger.info("DELETE /courses/%s/invite — удаление инвайт-ссылки", course.slug)
    invite = await invites_service.get_invite_ref_by_course_id(course.id, session)
    await invites_service.delete_invite_ref(invite, session)
    return ApiResponse.ok(
        data=None,
        message="Ссылка удалена",
        status_code=status.HTTP_200_OK,
    )
