"""Файл для создания FastAPI приложения"""

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


def create_app() -> FastAPI:
    docs_kwargs = {}
    if settings.ENVIRONMENT == "production":
        docs_kwargs = {"docs_url": None, "redoc_url": None, "openapi_url": None}

    app = FastAPI(
        title="platform_for_online_lesson",
        version="0.0.1",
        lifespan=app_lifespan,
        **docs_kwargs,  # type: ignore[arg-type]
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
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
