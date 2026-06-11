"""Файл для создания FastAPI приложения"""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..routers import auth_router, ws_chat_router
from .exception_handlers import http_exception_handler, validation_exception_handler
from .lifespan import app_lifespan


def create_app() -> FastAPI:
    app = FastAPI(
        title="platform_for_online_lesson",  # ИЗМЕНИТЬ ПРИ ВЫБОРЕ НАЗВАНИЯ СЕРВИСА
        version="0.0.1",
        lifespan=app_lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(ws_chat_router)
    app.include_router(auth_router)

    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]

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
