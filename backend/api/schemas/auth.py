"""Схемы для аутентификации"""

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegistrationSchema(BaseModel):
    email: EmailStr = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Логин пользователя",
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
    email: EmailStr = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Логин пользователя",
        json_schema_extra={"example": "example@example.com"},
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Пароль пользователя",
        json_schema_extra={"example": "superstrongandpowerfulpassword"},
    )


class TokenPairResponse(BaseModel):
    access_token: str = Field(..., description="Токен доступа к системе")
    refresh_token: str = Field(..., description="Токен обновления токена доступа")
    token_type: str = Field(default="bearer", description="Тип токена")


class RegistrationSuccessResponse(BaseModel):
    is_success: bool = Field(default=True, description="Флаг успешности")
    message: str = Field(default="Регистрация успешна", description="Сообщение")
    data: TokenPairResponse = Field(..., description="Выданные токены")


class RegistrationFailResponse(BaseModel):
    is_success: bool = Field(default=False, description="Флаг успешности")
    message: str = Field(..., description="Сообщение об ошибке")
    data: None = Field(default=None, description="Данные отсутствуют")
