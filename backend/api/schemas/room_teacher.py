"""Схемы для преподавателей комнаты"""

from datetime import datetime

from pydantic import BaseModel, Field


class AddRoomTeacher(BaseModel):
    room_id: int = Field(..., description="Идентификатор комнаты")
    user_id: int = Field(..., description="Идентификатор преподавателя")


class RoomTeacherRead(BaseModel):
    id: int
    room_id: int
    user_id: int
    added_by_user_id: int
    created_at: datetime
    updated_at: datetime


class RoomTeacherListItem(BaseModel):
    id: int
    room_id: int
    user_id: int
    created_at: datetime
