"""В этом файле создается асинхронный движок для БД"""

from collections.abc import AsyncGenerator
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel

from .config import settings


class Database:
    """
    Класс для управления подключением к БД, пулом соединений и сессиями.
    """

    def __init__(self) -> None:
        self.database_url = settings.DATABASE_URL
        self._engine: Optional[AsyncEngine] = None
        self._session_maker: Optional[async_sessionmaker[AsyncSession]] = None

    def connect(self) -> None:
        """
        Инициализирует движок и фабрику сессий.

        Вызывается один раз при старте приложения.
        """
        if self._engine is not None:
            return

        self._engine = create_async_engine(
            self.database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )

        self._session_maker = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def close(self) -> None:
        """
        Корректно закрывает пул соединений.
        """
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_maker = None

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        FastAPI-зависимость: выдаёт сессию и закрывает после запроса.
        """
        if self._session_maker is None:
            raise RuntimeError("База данных не инициализирована. Вызовите connect()")

        async with self._session_maker() as session:
            yield session

    async def create_tables(self) -> None:
        """Создание таблиц (удобно для тестов или первого запуска)."""
        if self._engine is None:
            raise RuntimeError("База данных не инициализирована")

        async with self._engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)


db = Database()
