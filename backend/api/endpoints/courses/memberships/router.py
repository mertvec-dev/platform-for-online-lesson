"""Роуты для управление участниками"""

import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from .....models import Course
from ....core import ApiResponse, db
from ....core.access_helpers import get_course_by_slug_or_404
from .schemas import (
    CourseMembershipListItem,
    RemoveMembers,
)
from .service import memberships_service

membership_router = APIRouter(tags=["courses-memberships"])

logger = logging.getLogger(__name__)


@membership_router.get(
    "/{slug}/members",
    summary="Список участников",
    response_model=ApiResponse[list[CourseMembershipListItem]],
)
async def get_members(
    course: Course = Depends(get_course_by_slug_or_404),
    session: AsyncSession = Depends(db.get_session),
):
    logger.info("GET /courses/%s/members — запрос списка участников", course.slug)
    members = await memberships_service.list_members(course.id, session)

    return ApiResponse.ok(
        data=members,
        message="Список участников",
        status_code=status.HTTP_200_OK,
    )


@membership_router.delete(
    "/{slug}/members",
    summary="Исключить участников",
    response_model=ApiResponse[None],
)
async def remove_members(
    body: RemoveMembers,
    course: Course = Depends(get_course_by_slug_or_404),
    session: AsyncSession = Depends(db.get_session),
):
    logger.info("DELETE /courses/%s/members — исключение участников", course.slug)
    await memberships_service.remove_members(course.id, body.user_ids, session)

    return ApiResponse.ok(
        data=None,
        message="Участники исключены.",
        status_code=status.HTTP_200_OK,
    )
