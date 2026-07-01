"""Роуты для присоединение к курсу по ссылке"""

# NOTE: В этом файле лежит ПРИСОЕДИНЕНИЕ К КУРСУ ПО ССЫЛКЕ

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....models import User
from ...core import db
from ...core.response import ApiResponse
from ..auth.dependencies import get_current_user
from ..courses.invites.schemas import JoinCourseByInvite
from ..courses.invites.service import invites_service

join_router = APIRouter(
    prefix="/invites",
    tags=["courses-join"],
)


@join_router.post(
    "/join",
    summary="Присоединится к курсу по ссылке",
    response_model=ApiResponse[None],
)
async def join_by_ref(
    body: JoinCourseByInvite,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    await invites_service.join_by_invites_ref(
        user_id=current_user.id,
        token=body.token,
        session=session,
    )

    return ApiResponse.ok(
        data=None,
        status_code=status.HTTP_200_OK,
        message="Вы успешно присоединились к курсу.",
    )
