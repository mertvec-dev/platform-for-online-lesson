"""Модель таблицы rooms_tokens"""

from datetime import datetime

from sqlmodel import Field, SQLModel


class RoomToken(SQLModel, table=True):
    """
    Модель для таблицы rooms_tokens

    Поля:
        id: int - Идентификатор токена
        rooms_id: int - Идентификатор комнаты
        user_id: int - Идентификатор пользователя
        token: str - Токен
        created_at: datetime - Дата и время создания токена
        expires_at: datetime - Дата и время истечения токена
    """

    # Название таблицы - rooms_tokens
    __tablename__ = "rooms_tokens"

    # Идентификатор токена
    id: int = Field(primary_key=True)

    # Идентификатор комнаты
    rooms_id: int = Field(foreign_key="rooms.id")

    # Идентификатор пользователя
    user_id: int = Field(foreign_key="users.id")

    # Токен
    token: str = Field()

    # Дата и время создания токена
    created_at: datetime = Field(default_factory=lambda: datetime.now())

    # Дата и время истечения токена
    expires_at: datetime = Field()
