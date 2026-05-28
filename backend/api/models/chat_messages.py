"""Модель таблицы chat_messages"""

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class ChatMessage(SQLModel, table=True):
    """
    Модель для таблицы chat_messages

    Поля:
        id: int - Идентификатор сообщения
        room_id: int - Идентификатор комнаты
        user_id: int - Идентификатор пользователя
        text: str - Текст сообщения
        created_at: datetime - Дата и время создания сообщения
    """

    # Название таблицы
    __tablename__ = "chat_messages"

    # Идентификатор сообщения
    id: int = Field(primary_key=True)

    # Идентификатор комнаты
    room_id: int = Field(foreign_key="rooms.id")

    # Идентификатор пользователя
    user_id: int = Field(foreign_key="users.id")

    # Текст сообщения
    text: str = Field()

    # Дата и время создания сообщения
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
