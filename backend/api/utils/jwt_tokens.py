"""JWT-токен утилиты"""

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from ...config import settings

security = HTTPBearer(auto_error=True)


def create_token(data: dict[str, Any], expires_in: int) -> str:
    """
    Создает JWT-токен.

    `expires_in` задается в секундах.
    """
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    payload.update({"exp": expire})

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
    except JWTError:
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

    payload = verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен не прошел верификацию",
        )

    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="В токене отсутствует user_id",
        )

    if not isinstance(user_id, int):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Некорректный user_id в токене",
        )

    return user_id
