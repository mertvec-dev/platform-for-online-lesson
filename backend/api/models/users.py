"""Модель для таблицы users"""

# Время
from datetime import datetime, timezone

# Перечисление
from enum import Enum

# Для модели таблицы
from sqlmodel import Field, SQLModel


class Role(str, Enum):  # Перечисление возможных ролей в системе
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class User(SQLModel, table=True):
    """
    Модель для таблицы users

    Поля:
        id: int - Идентификатор пользователя; Первичный ключ.
        first_name: str - Имя пользователя
        last_name: str - Фамилия пользователя
        password_hash: str - Хеш пароля пользователя
        email: str - Email пользователя
        role: Role - Роль пользователя (student, teacher, admin); По умолчанию student (для безопасности - принцип наименьших привилегий в случае обхода регистрации через учетную запись школы)
        created_at: datetime - Дата и время создания учетной записи пользователя
    """

    # Название таблицы - users
    __tablename__ = "users"

    # Идентификатор пользователя
    id: int = Field(primary_key=True, unique=True, index=True)

    first_name: str = Field()  # Имя пользователя
    last_name: str = Field()  # Фамилия пользователя
    password_hash: str = Field()  # Хэш пароля

    # logo_url: str | None = Field() # URL аватара пользователя (расскомментировать) | Пока не знаю, как будет выглядить профиль пользователя из школы

    # Почта пользователя
    email: str = Field(unique=True, index=True)
    # Роль пользователя в системе
    role: Role = Field(default=Role.STUDENT)  # Роль пользователя в системе

    # Дата регистрации пользователя в системе
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
