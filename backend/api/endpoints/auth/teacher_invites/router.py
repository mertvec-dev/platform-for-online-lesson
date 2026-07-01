"""Роуты управления инвайт-токенами преподавателей (только админ)"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .....models import User
from ....core import ApiResponse, db
from ..dependencies import require_admin
from .schemas import (
    CreateTeacherInvite,
    TeacherInviteListItem,
    TeacherInviteRead,
    UpdateTeacherInvite,
)
from .service import teacher_invite_service

teacher_invite_router = APIRouter(
    prefix="/admin/teacher-invites",
    tags=["admin-teacher-invites"],
    dependencies=[Depends(require_admin)],
)

logger = logging.getLogger(__name__)


@teacher_invite_router.post(
    "/",
    summary="Создать инвайт-токен для преподавателя",
    response_model=ApiResponse[TeacherInviteRead],
)
async def create_teacher_invite(
    body: CreateTeacherInvite,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(db.get_session),
):
    logger.info(
        "POST /admin/teacher-invites/ — создание инвайт-токена администратором %d",
        current_user.id,
    )
    invite = await teacher_invite_service.create(
        created_by=current_user.id,
        max_uses=body.max_uses,
        expires_at=body.expires_at,
        session=session,
    )
    return ApiResponse.ok(
        data=invite,
        message="Токен создан",
        status_code=status.HTTP_201_CREATED,
    )


@teacher_invite_router.get(
    "/",
    summary="Список всех инвайт-токенов",
    response_model=ApiResponse[list[TeacherInviteListItem]],
)
async def list_teacher_invites(
    session: AsyncSession = Depends(db.get_session),
):
    logger.info("GET /admin/teacher-invites/ — запрос списка инвайт-токенов")
    invites = await teacher_invite_service.list_all(session)
    return ApiResponse.ok(data=invites, message="Список токенов")


@teacher_invite_router.patch(
    "/{token}",
    summary="Обновить параметры токена",
    response_model=ApiResponse[TeacherInviteRead],
)
async def update_teacher_invite(
    token: str,
    body: UpdateTeacherInvite,
    session: AsyncSession = Depends(db.get_session),
):
    logger.info("PATCH /admin/teacher-invites/%s — обновление инвайт-токена", token)
    invite = await teacher_invite_service.get_by_token(token, session)
    if invite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Токен не найден.",
        )

    invite = await teacher_invite_service.update(
        invite=invite,
        is_active=body.is_active,
        max_uses=body.max_uses,
        expires_at=body.expires_at,
        session=session,
    )
    return ApiResponse.ok(data=invite, message="Токен обновлён")


@teacher_invite_router.delete(
    "/{token}",
    summary="Удалить токен",
    response_model=ApiResponse[None],
)
async def delete_teacher_invite(
    token: str,
    session: AsyncSession = Depends(db.get_session),
):
    logger.info("DELETE /admin/teacher-invites/%s — удаление инвайт-токена", token)
    invite = await teacher_invite_service.get_by_token(token, session)
    if invite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Токен не найден.",
        )

    await teacher_invite_service.delete(invite, session)
    return ApiResponse.ok(data=None, message="Токен удалён")
