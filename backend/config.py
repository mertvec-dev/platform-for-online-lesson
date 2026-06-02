"""Настройка приложения"""

from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET = "CHANGE_IT_IMMEDIATELY!!!"
MIN_PASSWORD_LENGTH = 12


class Config(BaseSettings):
    # === БАЗА ДАННЫХ ===
    POSTGRES_USER: str = Field(
        default="postgres", description="Имя пользователя PostgreSQL"
    )
    POSTGRES_PASSWORD: str = Field(
        default=DEFAULT_SECRET, description="Пароль PostgreSQL"
    )
    POSTGRES_DB: str = Field(default="db", description="Имя базы данных PostgreSQL")

    DATABASE_URL: str = ""

    # === Безопасность API ===
    WEBHOOK_SECRET: str = Field(
        default=DEFAULT_SECRET,
        description="Секрет для Livekit-webhook (проверка подлинности ответа)",
    )
    JWT_SECRET_KEY: str = Field(
        default=DEFAULT_SECRET,
        description="Секрет для проверки сигнатуры JWT-токена",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def model_post_init(self, __context):
        """Инициализация DATABASE_URL из переменных окружения, если в `.env` не указано значение"""
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@db:5432/{self.POSTGRES_DB}"

    @model_validator(mode="after")
    def check_security(self) -> Self:
        errors = []

        # Поля, которые не должны быть равны дефолту
        secret_fields = {
            "POSTGRES_PASSWORD": self.POSTGRES_PASSWORD,
            "WEBHOOK_SECRET": self.WEBHOOK_SECRET,
            "JWT_SECRET_KEY": self.JWT_SECRET_KEY,
        }

        for name, value in secret_fields.items():
            if value == DEFAULT_SECRET:
                errors.append(f"{name} — не переопределён в .env (остался дефолтным)")
            elif name == "POSTGRES_PASSWORD" and len(value) < MIN_PASSWORD_LENGTH:
                errors.append(
                    f"{name} — слишком короткий ({len(value)} < {MIN_PASSWORD_LENGTH} символов)"
                )

        if errors:
            raise ValueError(
                "Ошибки в конфигурации безопасности:\n  • " + "\n  • ".join(errors)
            )

        return self


settings = Config()
