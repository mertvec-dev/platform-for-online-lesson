"""Email-верификация: генерация кода, отправка, проверка"""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from secrets import randbelow

import aiosmtplib
from fastapi import HTTPException, status
from jinja2 import Environment, FileSystemLoader

from ...config import settings
from ..core import redis_client
from ..core.redis_keys import (
    CHECK_LIMIT,
    CHECK_WINDOW,
    CODE_TTL,
    SEND_LIMIT,
    SEND_WINDOW,
    email_verified_key,
    ratelimit_check_key,
    ratelimit_send_key,
    verify_code_key,
)

_templates_dir = Path(__file__).resolve().parent.parent / "templates" / "email"
_jinja = Environment(loader=FileSystemLoader(str(_templates_dir)))


def generate_verification_code() -> str:
    """6-значный код подтверждения (от 100000 до 999999)"""
    return str(randbelow(900000) + 100000)


async def request_verification(email: str) -> None:
    """
    Генерирует код → сохраняет в Redis → отправляет на почту.

    Rate-limit: не чаще 1 раза в SEND_WINDOW секунд.
    """
    count = await redis_client.incr_with_ttl(ratelimit_send_key(email), SEND_WINDOW)
    if count > SEND_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком много запросов. Попробуйте позже.",
        )

    code = generate_verification_code()
    await redis_client.set_cache(verify_code_key(email), code, expire=CODE_TTL)
    await send_verification_email(email, code)


async def verify_code(email: str, code: str) -> bool:
    """
    Сверяет код из Redis с переданным.

    Rate-limit: не более CHECK_LIMIT попыток за CHECK_WINDOW секунд.
    При успехе — удаляет код и ставит флаг email_verified (TTL как у кода).
    """
    count = await redis_client.incr_with_ttl(ratelimit_check_key(email), CHECK_WINDOW)
    if count > CHECK_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком много попыток. Попробуйте позже.",
        )

    stored = await redis_client.get_cache(verify_code_key(email))
    if stored is None:
        return False
    if stored != code:
        return False

    await redis_client.delete_cache(verify_code_key(email))
    # Ставим флаг — почта подтверждена (TTL как у кода, чтобы успеть зарегистрироваться)
    await redis_client.set_cache(email_verified_key(email), "1", expire=CODE_TTL)
    return True


async def is_email_verified(email: str) -> bool:
    """
    Проверяет, что почта была подтверждена.

    При успехе — удаляет флаг, чтобы нельзя было использовать повторно.
    """
    stored = await redis_client.get_cache(email_verified_key(email))
    if stored is None:
        return False
    await redis_client.delete_cache(email_verified_key(email))
    return True


async def send_verification_email(to_email: str, code: str) -> None:
    """Отправляет письмо с кодом подтверждения."""
    text_body = _jinja.get_template("verification.txt").render(
        code=code,
        app_name=settings.APP_NAME,
        ttl_minutes=settings.VERIFICATION_CODE_TTL_IN_MINUTES,
    )
    html_body = _jinja.get_template("verification.html").render(
        code=code,
        app_name=settings.APP_NAME,
        ttl_minutes=settings.VERIFICATION_CODE_TTL_IN_MINUTES,
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Код подтверждения — {settings.APP_NAME}"
    msg["From"] = str(settings.SMTP_FROM_EMAIL)
    msg["To"] = to_email
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    is_prod = settings.ENVIRONMENT == "production"
    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=str(settings.SMTP_FROM_EMAIL) if is_prod else None,
        password=settings.SMTP_PASSWORD if is_prod else None,
        use_tls=is_prod,
        start_tls=False,
    )
