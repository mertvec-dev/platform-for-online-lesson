"""Файл для создания FastAPI приложения"""

import contextvars
import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..core.config import settings
from ..core.response import ApiResponse
from ..endpoints.auth.router import auth_router
from ..endpoints.auth.teacher_invites.router import teacher_invite_router
from ..endpoints.chat.router import ws_router as ws_chat_router
from ..endpoints.courses.router import course_router
from ..endpoints.join.router import join_router
from ..endpoints.livekit.webhook import livekit_webhook_router
from ..endpoints.users.routers import user_router
from .exception_handlers import (
    http_exception_handler,
    integrity_error_handler,
    sqlalchemy_error_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from .lifespan import app_lifespan

MAX_REQUEST_BODY_SIZE = 1_048_576  # 1 MB

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default="-"
)


class RequestIDFilter(logging.Filter):
    """Внедряет request_id из ContextVar в каждую запись лога."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(request_id)-12s | %(name)-35s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def create_app() -> FastAPI:
    logging.basicConfig(
        level=logging.DEBUG if settings.ENVIRONMENT == "development" else logging.INFO,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
    )
    # Приглушаем шумные библиотеки
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    for handler in logging.root.handlers:
        handler.addFilter(RequestIDFilter())

    docs_kwargs = {}
    if settings.ENVIRONMENT == "production":
        docs_kwargs = {"docs_url": None, "redoc_url": None, "openapi_url": None}

    app = FastAPI(
        title="platform_for_online_lesson",
        version="0.0.1",
        lifespan=app_lifespan,
        **docs_kwargs,  # type: ignore[arg-type]
    )

    origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Middleware: лимит размера тела запроса (защита от memory exhaustion)
    @app.middleware("http")
    async def limit_body_size(request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_BODY_SIZE:
            return JSONResponse(
                status_code=413,
                content=ApiResponse.fail(
                    message="Тело запроса слишком большое",
                    status_code=413,
                ).model_dump(),
            )
        return await call_next(request)

    # Middleware: сквозной request_id для трассировки запросов в логах
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex[:12])
        request.state.request_id = request_id
        request_id_var.set(request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    app.include_router(ws_chat_router)
    app.include_router(auth_router)
    app.include_router(course_router)
    app.include_router(teacher_invite_router)
    app.include_router(join_router)
    app.include_router(livekit_webhook_router)
    app.include_router(user_router)

    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(IntegrityError, integrity_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)

    @app.get(
        "/",
        summary="Проверка работоспособности",
        description="Эндпоинт для проверки работоспособности сервиса",
    )
    async def root() -> dict[str, str]:
        return {
            "status": "LIVE",
            "message": "Service is running",
            "version": app.version,
        }

    return app
