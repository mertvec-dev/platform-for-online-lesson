"""Обработчики исключений

Все HTTPException оборачиваются в ApiResponse для единого формата ответа.
ValidationError от Pydantic — тоже.
"""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..core.response import ApiResponse


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse.fail(
            message=str(exc.detail),
            status_code=exc.status_code,
        ).model_dump(),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    messages = []
    for error in exc.errors():
        field = " → ".join(str(loc) for loc in error["loc"])
        messages.append(f"{field}: {error['msg']}")
    detail = "; ".join(messages)

    return JSONResponse(
        status_code=422,
        content=ApiResponse.fail(
            message=detail,
            status_code=422,
        ).model_dump(),
    )
