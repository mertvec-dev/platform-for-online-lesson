"""Схемы для аутентификации"""

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegistrationSchema(BaseModel):
    email: EmailStr = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Email пользователя",
        json_schema_extra={"example": "example@example.com"},
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Пароль пользователя",
        json_schema_extra={"example": "superstrongpassword"},
    )
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Имя пользователя",
        json_schema_extra={"example": "John"},
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Фамилия пользователя",
        json_schema_extra={"example": "Doe"},
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Пароль должен содержать не менее 8 символов")
        return value


class AuthSchema(BaseModel):
    """Логин — email + пароль"""

    email: EmailStr = Field(
        ...,
        description="Email пользователя",
        json_schema_extra={"example": "user@example.com"},
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Пароль пользователя",
        json_schema_extra={"example": "superstrongandpowerfulpassword"},
    )


class TokenPair(BaseModel):
    """Пара access + refresh токенов"""

    access_token: str = Field(..., description="Токен доступа")
    refresh_token: str = Field(..., description="Токен обновления")
    token_type: str = Field(default="bearer", description="Тип токена")
