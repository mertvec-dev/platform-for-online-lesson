"""Роуты аутентификации"""

import logging

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core import db, redis_client
from ...core.config import settings
from ...core.redis_keys import (
    LOGIN_IP_LIMIT,
    LOGIN_IP_WINDOW,
    REGISTER_IP_LIMIT,
    REGISTER_IP_WINDOW,
    ratelimit_login_ip_key,
    ratelimit_register_ip_key,
)
from ...core.response import ApiResponse
from .schemas import (
    AuthSchema,
    RefreshTokenSchema,
    RegistrationSchema,
    TokenPair,
    VerifyEmailSchema,
)
from .service import auth_service

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

logger = logging.getLogger(__name__)


def _set_auth_cookies(response: Response, token_pair: TokenPair) -> None:
    """Ставит httponly куки с access и refresh токенами."""
    secure = settings.ENVIRONMENT == "production"
    response.set_cookie(
        key="access_token",
        value=token_pair.access_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=settings.ACCESS_JWT_TOKEN_EXPIRES_IN_SECONDS,
    )
    response.set_cookie(
        key="refresh_token",
        value=token_pair.refresh_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=settings.REFRESH_JWT_TOKEN_EXPIRES_IN_SECONDS,
    )


def _client_ip(request: Request) -> str:
    """Извлекает IP клиента, учитывая X-Forwarded-For."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@auth_router.post(
    "/register",
    summary="Регистрация",
)
async def register(
    body: RegistrationSchema,
    request: Request,
    session: AsyncSession = Depends(db.get_session),
):
    """Сохраняет данные в Redis и отправляет код подтверждения на почту."""
    logger.info("POST /auth/register — регистрация пользователя %s", body.email)
    ip = _client_ip(request)
    count = await redis_client.incr_with_ttl(
        ratelimit_register_ip_key(ip), REGISTER_IP_WINDOW
    )
    if count > REGISTER_IP_LIMIT:
        return ApiResponse.fail(
            message="Слишком много запросов. Попробуйте позже.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    await auth_service.request_registration(
        email=body.email,
        password=body.password,
        first_name=body.first_name,
        last_name=body.last_name,
        teacher_invite_token=body.teacher_invite_token,
        db_session=session,
    )
    return ApiResponse.ok(
        data=None,
        message=f"Код подтверждения отправлен на {body.email}",
        status_code=200,
    )


@auth_router.post(
    "/verify",
    summary="Подтвердить почту и завершить регистрацию",
    response_model=ApiResponse[TokenPair],
)
async def verify_email(
    body: VerifyEmailSchema,
    response: Response,
    session: AsyncSession = Depends(db.get_session),
):
    """Сверяет код, создаёт пользователя в БД, возвращает токены."""
    logger.info("POST /auth/verify — подтверждение почты %s", body.email)
    token_pair = await auth_service.confirm_registration(
        email=body.email,
        code=body.code,
        db_session=session,
    )
    _set_auth_cookies(response, token_pair)
    return ApiResponse.ok(
        data=token_pair,
        message="Регистрация завершена",
        status_code=status.HTTP_201_CREATED,
    )


@auth_router.post(
    "/login",
    summary="Вход",
    response_model=ApiResponse[TokenPair],
)
async def login(
    body: AuthSchema,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(db.get_session),
):
    """Аутентифицирует пользователя и возвращает пару токенов."""
    logger.info("POST /auth/login — вход пользователя %s", body.email)
    ip = _client_ip(request)
    count = await redis_client.incr_with_ttl(
        ratelimit_login_ip_key(ip), LOGIN_IP_WINDOW
    )
    if count > LOGIN_IP_LIMIT:
        return ApiResponse.fail(
            message="Слишком много попыток входа. Попробуйте позже.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    token_pair = await auth_service.login(
        email=body.email,
        password=body.password,
        db_session=session,
    )
    _set_auth_cookies(response, token_pair)
    return ApiResponse.ok(
        data=token_pair,
        message="Вход выполнен",
    )


@auth_router.post(
    "/refresh",
    summary="Обновить токены",
    response_model=ApiResponse[TokenPair],
)
async def refresh(
    body: RefreshTokenSchema,
    response: Response,
    session: AsyncSession = Depends(db.get_session),
):
    """Обновляет пару токенов по refresh-токену. Старый jti отзывается."""
    logger.info("POST /auth/refresh — обновление токенов")
    token_pair = await auth_service.refresh_token(
        token=body.refresh_token,
        db_session=session,
    )
    _set_auth_cookies(response, token_pair)
    return ApiResponse.ok(
        data=token_pair,
        message="Токены обновлены",
    )
