"""
Тестовые фикстуры.

Каждый тест получает чистую SQLite БД in-memory.
"""

from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

TEST_DATABASE_URL = "sqlite+aiosqlite://"

_test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=_test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Чистая БД для каждого теста."""
    async with _test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with TestSessionLocal() as s:
        yield s

    async with _test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture(scope="session")
async def client() -> AsyncGenerator:
    """HTTP-клиент для тестирования эндпоинтов."""
    from httpx import ASGITransport, AsyncClient

    # Подменяем БД на тестовую ДО импорта приложения
    from backend.api.core import db as db_instance

    db_instance._engine = _test_engine
    db_instance._session_maker = TestSessionLocal

    # Блокируем create_tables — таблицы создаются фикстурой
    db_instance.create_tables = lambda self=None: None  # type: ignore[assignment]

    from backend.api.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
