"""Роуты аутентификации"""

from fastapi import APIRouter, HTTPException, status

from ..utils import request_verification, verify_code

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@auth_router.post("/request-code", summary="Запросить код подтверждения")
async def request_verification_code(email: str):
    """Отправляет код на email. В dev идёт через Mailpit."""
    await request_verification(email)
    return {"message": f"Код отправлен на {email}"}


@auth_router.post("/verify-code", summary="Подтвердить код из письма")
async def verify_verification_code(email: str, code: str):
    """Сверяет код. При успехе почта помечается как подтверждённая."""
    if await verify_code(email, code):
        return {"message": "Код подтверждён"}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Неверный код подтверждения",
    )
