"""Общая пагинация для list-эндпоинтов."""

from typing import TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class PaginationParams:
    """Зависимость: извлекает limit/offset из query-параметров."""

    def __init__(
        self,
        limit: int = DEFAULT_PAGE_SIZE,
        offset: int = 0,
    ) -> None:
        self.limit = min(max(limit, 1), MAX_PAGE_SIZE)
        self.offset = max(offset, 0)


class PaginatedResponse(BaseModel):
    """Метаданные пагинации (опционально — можно добавить total/count позже)."""

    limit: int = Field(..., description="Размер страницы")
    offset: int = Field(..., description="Смещение от начала")
