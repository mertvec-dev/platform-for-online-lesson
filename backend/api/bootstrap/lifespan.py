"""Файл управляет жизненным циклом приложения"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from ..core import db, redis_client
from ..core.webhook_worker import worker
from ..core.websocket import websocket_manager
from .pre_startup import run_tests
from .seed import seed_default_admin

logger = logging.getLogger(__name__)


@asynccontextmanager
async def app_lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Запуск приложения")
    run_tests()
    db.connect()
    await db.create_tables()
    async with db.session() as seed_session:
        await seed_default_admin(seed_session)
    redis_client.connect()
    worker.connect_db(db)
    await worker.start()
    logger.info("Приложение готово к работе")

    yield

    logger.info("Остановка приложения")
    await websocket_manager.shutdown()
    await worker.stop()
    await redis_client.close()
    await db.close()
    logger.info("Приложение остановлено")
