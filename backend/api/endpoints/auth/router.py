"""Роуты аутентификации"""

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ...core import db
from ...core.config import settings
from ...core.response import ApiResponse
from .schemas import AuthSchema, RegistrationSchema, TokenPair
from .service import auth_service

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


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


@auth_router.post(
    "/register",
    summary="Регистрация",
)
async def register(
    body: RegistrationSchema,
    session: AsyncSession = Depends(db.get_session),
):
    """Сохраняет данные в Redis и отправляет код подтверждения на почту."""
    await auth_service.request_registration(
        email=body.email,
        password=body.password,
        first_name=body.first_name,
        last_name=body.last_name,
        db_session=session,
    )
    return {"message": f"Код подтверждения отправлен на {body.email}"}


@auth_router.post(
    "/verify",
    summary="Подтвердить почту и завершить регистрацию",
    response_model=ApiResponse[TokenPair],
)
async def verify_email(
    email: str,
    code: str,
    response: Response,
    session: AsyncSession = Depends(db.get_session),
):
    """Сверяет код, создаёт пользователя в БД, возвращает токены."""
    token_pair = await auth_service.confirm_registration(
        email=email,
        code=code,
        db_session=session,
    )
    _set_auth_cookies(response, token_pair)
    return ApiResponse.ok(
        data=token_pair,
        message="Регистрация завершена",
        status_code=201,
    )


@auth_router.post(
    "/login",
    summary="Вход",
    response_model=ApiResponse[TokenPair],
)
async def login(
    body: AuthSchema,
    response: Response,
    session: AsyncSession = Depends(db.get_session),
):
    """Аутентифицирует пользователя и возвращает пару токенов."""
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
    response: Response,
    refresh_token: str,
    session: AsyncSession = Depends(db.get_session),
):
    """Обновляет пару токенов по refresh-токену. Старый jti отзывается."""
    token_pair = await auth_service.refresh_token(
        token=refresh_token,
        db_session=session,
    )
    _set_auth_cookies(response, token_pair)
    return ApiResponse.ok(
        data=token_pair,
        message="Токены обновлены",
    )
