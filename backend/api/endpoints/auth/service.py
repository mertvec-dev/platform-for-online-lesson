"""Сервисы аутентификации"""

import logging

from bcrypt import checkpw, gensalt, hashpw
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....models import User
from ....models.users import Role
from ...core import redis_client
from ...core.config import settings
from ...core.redis_keys import (
    CODE_TTL,
    refresh_jti_key,
    registration_key,
)
from .email_auth import request_verification, verify_code
from .jwt_tokens import create_token, extract_user_id, verify_token
from .schemas import TokenPair
from .teacher_invites.service import teacher_invite_service

logger = logging.getLogger(__name__)


class AuthService:
    async def _make_token_pair(self, user_id: int) -> TokenPair:
        """Создаёт пару токенов и сохраняет refresh jti в Redis-whitelist."""
        access_token = create_token(
            {"user_id": user_id},
            expires_in=settings.ACCESS_JWT_TOKEN_EXPIRES_IN_SECONDS,
        )
        refresh_token = create_token(
            {"user_id": user_id},
            expires_in=settings.REFRESH_JWT_TOKEN_EXPIRES_IN_SECONDS,
        )

        payload = verify_token(refresh_token)
        jti = payload["jti"] if payload else None
        if jti:
            await redis_client.set_cache(
                refresh_jti_key(jti),
                str(user_id),
                expire=settings.REFRESH_JWT_TOKEN_EXPIRES_IN_SECONDS,
            )

        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    async def request_registration(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        teacher_invite_token: str | None,
        db_session: AsyncSession,
    ) -> None:
        """Сохраняет данные в Redis и отправляет код на почту."""
        existing = await db_session.execute(
            select(User).where(User.email == email)  # type: ignore[arg-type]
        )
        if existing.scalar():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Пользователь с такой почтой уже существует",
            )

        hashed_password = hashpw(password.encode(), gensalt()).decode()
        invite_part = teacher_invite_token or ""
        await redis_client.set_cache(
            registration_key(email),
            f"{hashed_password}|{first_name}|{last_name}|{invite_part}",
            expire=CODE_TTL,
        )

        await request_verification(email)
        logger.info("Запрошена регистрация для email=%s", email)

    async def confirm_registration(
        self,
        email: str,
        code: str,
        db_session: AsyncSession,
    ) -> TokenPair:
        """Сверяет код, создаёт пользователя в БД, возвращает токены."""
        if not await verify_code(email, code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный или истёкший код подтверждения",
            )

        reg_data = await redis_client.get_cache(registration_key(email))
        if reg_data is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Данные регистрации истекли. Зарегистрируйтесь заново.",
            )

        parts = reg_data.split("|")
        password_hash = parts[0]
        first_name = parts[1]
        last_name = parts[2]
        teacher_invite_token = parts[3] if len(parts) > 3 and parts[3] else None

        existing = await db_session.execute(
            select(User).where(User.email == email)  # type: ignore[arg-type]
        )
        if existing.scalar():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Пользователь с такой почтой уже существует",
            )

        user = User(
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
        )
        db_session.add(user)
        await db_session.flush()

        if teacher_invite_token:
            invite = await teacher_invite_service.validate_and_consume(
                teacher_invite_token, db_session
            )
            user.role = Role.TEACHER
            invite.used_count += 1
            await db_session.commit()
        else:
            await db_session.commit()

        await redis_client.delete_cache(registration_key(email))

        token_pair = await self._make_token_pair(user.id)
        logger.info("Подтверждена регистрация: user_id=%d, email=%s", user.id, email)
        return token_pair

    async def login(
        self,
        email: str,
        password: str,
        db_session: AsyncSession,
    ) -> TokenPair:
        result = await db_session.execute(
            select(User).where(User.email == email)  # type: ignore[arg-type]
        )
        user = result.scalar()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверные учетные данные",
            )

        if not checkpw(password.encode(), user.password_hash.encode()):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверные учетные данные",
            )

        token_pair = await self._make_token_pair(user.id)
        logger.info("Пользователь user_id=%d вошёл в систему", user.id)
        return token_pair

    async def refresh_token(
        self,
        token: str,
        db_session: AsyncSession,
    ) -> TokenPair:
        payload = verify_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Невалидный или истёкший refresh-токен",
            )

        jti = payload.get("jti")
        if not jti:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="В токене отсутствует jti",
            )

        if await redis_client.get_cache(refresh_jti_key(jti)) is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh-токен уже был использован или отозван",
            )

        await redis_client.delete_cache(refresh_jti_key(jti))

        user_id = extract_user_id(token)
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный refresh-токен",
            )

        user = await db_session.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден",
            )

        token_pair = await self._make_token_pair(user.id)
        logger.info("Refresh-токен обновлён для user_id=%d", user.id)
        return token_pair


auth_service = AuthService()
