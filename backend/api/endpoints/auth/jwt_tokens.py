"""JWT-токен утилиты"""

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from ...core.config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=True)


def create_token(data: dict[str, Any], expires_in: int) -> str:
    """
    Создает JWT-токен с уникальным jti.

    `expires_in` задается в секундах.
    """
    payload = data.copy()
    expire = datetime.now(UTC) + timedelta(seconds=expires_in)
    payload.update({"exp": expire, "jti": uuid.uuid4().hex})

    return jwt.encode(
        claims=payload,
        key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def verify_token(token: str) -> dict[str, Any] | None:
    """
    Проверяет JWT-токен.

    Возвращает payload токена или `None`, если токен невалиден или истёк.
    """
    try:
        return jwt.decode(
            token=token,
            key=settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as exc:
        logger.warning("JWT-верификация провалена: %s", exc)
        return None


def extract_user_id(token: str) -> int | None:
    """
    Извлекает user_id из JWT-токена.

    Возвращает user_id или None, если токен невалиден или user_id повреждён.
    """
    payload = verify_token(token)
    if payload is None:
        return None
    user_id = payload.get("user_id")
    if isinstance(user_id, int):
        return user_id
    return None


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> int:
    """
    FastAPI-зависимость, извлекающая `user_id` из Bearer JWT-токена.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Нет заголовка Authorization",
        )

    user_id = extract_user_id(credentials.credentials)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен не прошел верификацию",
        )

    return user_id
