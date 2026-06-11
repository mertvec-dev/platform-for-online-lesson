"""Сервисы аутентификации"""

from bcrypt import checkpw, gensalt, hashpw
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import settings
from ..core import redis_client
from ..core.redis_keys import refresh_jti_key
from ..models import User
from ..schemas import TokenPair
from ..utils import create_token, extract_user_id, verify_token
from ..utils.email_auth import is_email_verified


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

    async def register(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        db_session: AsyncSession,
    ) -> TokenPair:
        if not await is_email_verified(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Почта не подтверждена. Сначала запросите код.",
            )

        result = await db_session.execute(
            select(User).where(User.email == email)  # type: ignore[arg-type]
        )
        if result.scalar():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь уже существует",
            )

        hashed_password = hashpw(password.encode(), gensalt()).decode()
        new_user = User(
            email=email,
            password_hash=hashed_password,
            first_name=first_name,
            last_name=last_name,
        )
        db_session.add(new_user)
        await db_session.commit()
        assert new_user.id is not None

        return await self._make_token_pair(new_user.id)

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
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден",
            )

        if not checkpw(password.encode(), user.password_hash.encode()):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверные учетные данные",
            )

        assert user.id is not None
        return await self._make_token_pair(user.id)

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

        assert user.id is not None
        return await self._make_token_pair(user.id)
