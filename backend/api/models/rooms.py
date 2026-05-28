"""Модель таблицы rooms"""

# Время
from datetime import datetime, timezone
from typing import TYPE_CHECKING

# Для модели таблицы
from sqlmodel import Field, SQLModel
from sqlmodel.main import Relationship

if TYPE_CHECKING:
    from .chat_messages import ChatMessage
    from .users import User


class Room(SQLModel, table=True):
    """
    Модель для таблицы rooms

    Поля:
        id: int - Идентификатор комнаты; Первичный ключ
        teacher_id: int - Идентификатор преподавателя; Внешний ключ (c таблицы users)
        slug: str - Ссылка комнаты; Уникальный идентификатор комнаты
        max_participants: int - Максимальное количество участников; По умолчанию 50
        created_at: datetime - Дата и время создания комнаты; По умолчанию текущее время
        is_active: bool - Флаг активности комнаты; По умолчанию True
    """

    # Название таблицы
    __tablename__ = "rooms"

    # Идентификатор комнаты
    id: int = Field(primary_key=True, unique=True, index=True)

    # Идентификатор преподавателя
    teacher_id: int = Field(foreign_key="users.id")

    # Ссылка на занятие (генерируется каждый разв слое API, по uuid4)
    # Например, https://lesson.com/rooms/<uuid4>
    slug: str = Field()

    # Максимальное количество участников
    max_participants: int = Field(default=50)

    # Дата и время создания комнаты
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Флаг активности комнаты
    is_active: bool = Field(default=True)

    # Далее идут поля, которые могут быть использованы (расскоментировать, если нужно)
    # started_at: datetime # Когда занятие началось
    # ended_at: datetime # Когда занятие завершилось
    # title: str # Название занятия

    # Отношения таблиц
    teacher: "User" = Relationship(back_populates="rooms")
    messages: list["ChatMessage"] = Relationship(back_populates="room")
