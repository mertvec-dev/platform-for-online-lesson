"""Файл для создания FastAPI приложения"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# from ...config import settings # <-- Расскомментировать, когда будут готовы CORS политики
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

    @app.get(
        "/",
        summary="Проверка работоспособности",
        description="Эндпоинт для проверки работоспособности сервиса",
    )
    async def root() -> dict:
        return {
            "status": "LIVE",
            "message": "Service is running",
            "version": app.version,
        }

    return app
