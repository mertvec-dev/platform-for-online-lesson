"""Схемы для пользователей"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from ....models.users import Role


class UserRead(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    role: Role
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserListItem(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    role: Role
    is_active: bool


class UpdateUser(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)


class UpdateUserByAdmin(UpdateUser):
    email: EmailStr | None = Field(default=None)
    role: Role | None = Field(default=None)
    is_active: bool | None = Field(default=None)


class UserIdsPayload(BaseModel):
    user_ids: list[int] = Field(..., min_length=1, max_length=100)


class SetActivePayload(UserIdsPayload):
    is_active: bool = Field(...)
