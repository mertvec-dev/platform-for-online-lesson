"""Роуты профилей пользователей"""

import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....models import User
from ...core import ApiResponse, db
from ...core.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from ..auth.dependencies import get_current_user, require_admin
from .schemas import (
    SetActivePayload,
    UpdateUser,
    UpdateUserByAdmin,
    UserIdsPayload,
    UserListItem,
    UserRead,
)
from .service import user_service

user_router = APIRouter(prefix="/users", tags=["users"])

logger = logging.getLogger(__name__)


@user_router.get(
    "/me",
    summary="Мой профиль",
    response_model=ApiResponse[UserRead],
)
async def get_me(current_user: User = Depends(get_current_user)):
    logger.info(
        "GET /users/me — запрос своего профиля, пользователь %d", current_user.id
    )
    return ApiResponse.ok(
        data=current_user,
        message="Ваш профиль",
        status_code=status.HTTP_200_OK,
    )


@user_router.patch(
    "/me",
    summary="Обновить профиль",
    response_model=ApiResponse[UserRead],
)
async def update_me(
    body: UpdateUser,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    logger.info(
        "PATCH /users/me — обновление своего профиля, пользователь %d", current_user.id
    )
    user = await user_service.update_user(
        user=current_user,
        first_name=body.first_name,
        last_name=body.last_name,
        email=None,
        role=None,
        is_active=None,
        session=session,
    )
    return ApiResponse.ok(
        data=user,
        message="Профиль обновлён",
        status_code=status.HTTP_200_OK,
    )


@user_router.get(
    "/",
    summary="Список пользователей (админ)",
    response_model=ApiResponse[list[UserListItem]],
    dependencies=[Depends(require_admin)],
)
async def get_users(
    session: AsyncSession = Depends(db.get_session),
    limit: int = DEFAULT_PAGE_SIZE,
    offset: int = 0,
):
    logger.info(
        "GET /users/ — запрос списка пользователей (limit=%d, offset=%d)", limit, offset
    )
    users = await user_service.get_users(
        session, limit=min(limit, MAX_PAGE_SIZE), offset=offset
    )
    return ApiResponse.ok(
        data=users,
        message="Список пользователей",
        status_code=status.HTTP_200_OK,
    )


@user_router.get(
    "/{user_id}",
    summary="Пользователь по ID (админ)",
    response_model=ApiResponse[UserRead],
    dependencies=[Depends(require_admin)],
)
async def get_user_by_id(
    user_id: int,
    session: AsyncSession = Depends(db.get_session),
):
    logger.info("GET /users/%d — запрос пользователя", user_id)
    user = await user_service.get_user(user_id, session)
    return ApiResponse.ok(
        data=user,
        message="Профиль пользователя",
        status_code=status.HTTP_200_OK,
    )


@user_router.patch(
    "/{user_id}",
    summary="Изменить пользователя (админ)",
    response_model=ApiResponse[UserRead],
    dependencies=[Depends(require_admin)],
)
async def update_user_by_admin(
    user_id: int,
    body: UpdateUserByAdmin,
    session: AsyncSession = Depends(db.get_session),
):
    logger.info("PATCH /users/%d — изменение пользователя администратором", user_id)
    user = await user_service.get_user(user_id, session)
    user = await user_service.update_user(
        user=user,
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email,
        role=body.role,
        is_active=body.is_active,
        session=session,
    )
    return ApiResponse.ok(
        data=user,
        message="Пользователь обновлён",
        status_code=status.HTTP_200_OK,
    )


@user_router.post(
    "/set-active",
    summary="Активировать/деактивировать пользователей (админ)",
    response_model=ApiResponse[None],
    dependencies=[Depends(require_admin)],
)
async def set_users_active(
    body: SetActivePayload,
    session: AsyncSession = Depends(db.get_session),
):
    logger.info(
        "POST /users/set-active — изменение статуса пользователей: %s", body.user_ids
    )
    await user_service.set_users_active(
        users_ids=body.user_ids,
        is_active=body.is_active,
        session=session,
    )
    return ApiResponse.ok(
        data=None,
        message="Статусы обновлены",
        status_code=status.HTTP_200_OK,
    )


@user_router.post(
    "/delete",
    summary="Удалить пользователей (админ)",
    response_model=ApiResponse[None],
    dependencies=[Depends(require_admin)],
)
async def delete_users(
    body: UserIdsPayload,
    session: AsyncSession = Depends(db.get_session),
):
    logger.info("POST /users/delete — удаление пользователей: %s", body.user_ids)
    await user_service.delete_users(body.user_ids, session)
    return ApiResponse.ok(
        data=None,
        message="Пользователи удалены",
        status_code=status.HTTP_200_OK,
    )
