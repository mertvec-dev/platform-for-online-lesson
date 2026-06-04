"""Файл управляет жизненным циклом приложения"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from ..core import db, redis_client


@asynccontextmanager
async def app_lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    # startup
    db.connect()
    await db.create_tables()
    redis_client.connect()

    yield

    # shutdown
    await redis_client.close()
    await db.close()
