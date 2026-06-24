"""Единая обёртка ответа API

Все эндпоинты возвращают ApiResponse[T] или ApiResponse[None] для ошибок.
"""

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    is_success: bool = Field(..., description="Флаг успешности")
    message: str = Field(..., description="Сообщение")
    status_code: int = Field(..., description="HTTP-код ответа")
    data: Optional[T] = Field(default=None, description="Полезная нагрузка")

    @classmethod
    def ok(cls, data: T, message: str = "OK", status_code: int = 200):
        return cls(
            is_success=True,
            message=message,
            status_code=status_code,
            data=data,
        )

    @classmethod
    def fail(cls, message: str, status_code: int = 400):
        return cls(
            is_success=False,
            message=message,
            status_code=status_code,
            data=None,
        )
