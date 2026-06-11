"""Настройка приложения"""

from enum import Enum
from typing import Self

from pydantic import EmailStr, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET = "CHANGE_IT_IMMEDIATELY!!!"
DEFAULT_EMAIL = "noreply@example.com"
MIN_PASSWORD_LENGTH = 12


class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class Config(BaseSettings):
    APP_NAME: str = Field(default="МояПлатформа", description="Название приложения")
    ENVIRONMENT: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Окружение: development или production",
    )

    # === БАЗА ДАННЫХ ===
    DATABASE_HOST: str = Field(default="database", description="Хост PostgreSQL")
    POSTGRES_USER: str = Field(
        default="postgres", description="Имя пользователя PostgreSQL"
    )
    POSTGRES_PASSWORD: str = Field(
        default=DEFAULT_SECRET, description="Пароль PostgreSQL"
    )
    POSTGRES_DB: str = Field(default="db", description="Имя базы данных PostgreSQL")

    DATABASE_URL: str = ""

    # === Redis ===
    REDIS_HOST: str = Field(default="redis", description="Хост Redis")
    REDIS_PORT: int = Field(default=6379, description="Порт Redis")
    REDIS_PASSWORD: str = Field(default=DEFAULT_SECRET, description="Пароль Redis")

    # === Безопасность API ===
    VERIFICATION_CODE_TTL_IN_MINUTES: int = Field(
        default=5,
        description="Время жизни кода подтверждения в минутах",
    )
    WEBHOOK_SECRET: str = Field(
        default=DEFAULT_SECRET,
        description="Секрет для Livekit-webhook (проверка подлинности ответа)",
    )
    JWT_SECRET_KEY: str = Field(
        default=DEFAULT_SECRET,
        description="Секрет для проверки сигнатуры JWT-токена",
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="Алгоритм для проверки сигнатуры JWT-токена",
    )
    ACCESS_JWT_TOKEN_EXPIRES_IN_MINUTES: int = Field(
        default=30,
        description="Время жизни access JWT-токена в минутах",
    )
    REFRESH_JWT_TOKEN_EXPIRES_IN_DAYS: int = Field(
        default=7,
        description="Время жизни refresh JWT-токена в днях",
    )

    @property
    def ACCESS_JWT_TOKEN_EXPIRES_IN_SECONDS(self) -> int:
        """Access-токен: минуты → секунды"""
        return self.ACCESS_JWT_TOKEN_EXPIRES_IN_MINUTES * 60

    @property
    def REFRESH_JWT_TOKEN_EXPIRES_IN_SECONDS(self) -> int:
        """Refresh-токен: дни → секунды"""
        return self.REFRESH_JWT_TOKEN_EXPIRES_IN_DAYS * 86400

    # === SMTP (почта) ===
    SMTP_HOST: str = Field(default="smtp.yandex.ru", description="SMTP-хост")
    SMTP_PORT: int = Field(default=465, description="SMTP-порт")
    SMTP_FROM_EMAIL: EmailStr = Field(
        default=DEFAULT_EMAIL,
        description="Адрес отправителя",
    )
    SMTP_PASSWORD: str = Field(default=DEFAULT_SECRET, description="Пароль SMTP")

    # === CORS ===
    # ALLOWED_ORIGINS: list[str] = Field(
    #     default=["http://localhost:443"],
    #     description="Список разрешенных источников (CORS)",
    # )

    def model_post_init(self, __context):
        """Инициализация DATABASE_URL и переключение настроек под окружение"""
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:"
                f"{self.POSTGRES_PASSWORD}@{self.DATABASE_HOST}:5432/{self.POSTGRES_DB}"
            )

        if self.ENVIRONMENT == Environment.DEVELOPMENT:
            self.SMTP_HOST = "mailpit"
            self.SMTP_PORT = 1025
            self.SMTP_PASSWORD = "any"  # Mailpit не требует пароля

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def check_security(self) -> Self:
        errors = []

        # Поля, которые не должны быть равны дефолту
        secret_fields: dict[str, str] = {
            "POSTGRES_PASSWORD": self.POSTGRES_PASSWORD,
            "WEBHOOK_SECRET": self.WEBHOOK_SECRET,
            "JWT_SECRET_KEY": self.JWT_SECRET_KEY,
            "REDIS_PASSWORD": self.REDIS_PASSWORD,
        }

        if self.ENVIRONMENT == Environment.PRODUCTION:
            secret_fields["SMTP_PASSWORD"] = self.SMTP_PASSWORD

        for name, value in secret_fields.items():
            if value == DEFAULT_SECRET:
                errors.append(f"{name} — не переопределён в .env (остался дефолтным)")
            elif name == "POSTGRES_PASSWORD" and len(value) < MIN_PASSWORD_LENGTH:
                errors.append(
                    f"{name} — слишком короткий "
                    f"({len(value)} < {MIN_PASSWORD_LENGTH} символов)"
                )

        if errors:
            raise ValueError(
                "Ошибки в конфигурации безопасности:\n  • " + "\n  • ".join(errors)
            )

        return self


settings = Config()
