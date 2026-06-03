"""JWT-токен утилиты"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import ExpiredSignatureError, JWTError, jwt

from ...config import settings


def create_access_token(data: dict[str, Any], expires_in: int) -> str:
    """
    Создает JWT-токен

    - `expires_in` - сколько действует токен (в секундах)
    """
    payload = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    payload.update({"exp": expire})

    token = jwt.encode(
        claims=payload, key=settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return token


def verify_token(token: str) -> dict[str, Any] | None:
    """
    Декодирует и проверяет JWT-токен

    Возвращает `payload` токена или:
        - Если токен просрочен - `Ex`
        - Подпись не совпадает
    """
    try:
        payload = jwt.decode(
            token=token,
            key=settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        return payload
    except (ExpiredSignatureError, JWTError):
        return None
