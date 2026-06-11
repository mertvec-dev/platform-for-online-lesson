"""Схемы для пользователей"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from ..models.users import Role


class UserRead(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    role: Role
    is_active: bool
    deactivated_at: datetime | None
    created_at: datetime
    updated_at: datetime


class UserListItem(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    role: Role


class UpdateUser(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    role: Role | None = Field(default=None)
    is_active: bool | None = Field(default=None)
