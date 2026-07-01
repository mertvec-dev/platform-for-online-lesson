"""Обработчики исключений

Все HTTPException оборачиваются в ApiResponse для единого формата ответа.
ValidationError от Pydantic — тоже.
Необработанные исключения (БД, IntegrityError и пр.) логируются.
"""

import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..core.response import ApiResponse

logger = logging.getLogger(__name__)


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


async def integrity_error_handler(
    request: Request, exc: IntegrityError
) -> JSONResponse:
    logger.warning(
        "Ограничение целостности нарушено. Метод %s, путь %s",
        request.method,
        request.url.path,
        exc_info=True,
    )
    return JSONResponse(
        status_code=409,
        content=ApiResponse.fail(
            message="Операция невозможна: нарушено ограничение целостности данных.",
            status_code=409,
        ).model_dump(),
    )


async def sqlalchemy_error_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    logger.error(
        "Ошибка базы данных. Метод %s, путь %s",
        request.method,
        request.url.path,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content=ApiResponse.fail(
            message="Внутренняя ошибка при обращении к базе данных.",
            status_code=500,
        ).model_dump(),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.critical(
        "Необработанное исключение. Метод %s, путь %s",
        request.method,
        request.url.path,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content=ApiResponse.fail(
            message="Произошла непредвиденная ошибка.",
            status_code=500,
        ).model_dump(),
    )
