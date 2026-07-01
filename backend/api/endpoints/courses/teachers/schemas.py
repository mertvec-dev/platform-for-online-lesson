"""Схемы для преподавателей курса"""

from datetime import datetime

from pydantic import BaseModel, Field


class AddCourseTeachers(BaseModel):
    user_ids: list[int] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Идентификаторы преподавателей",
    )


class DeleteCourseTeachers(BaseModel):
    user_ids: list[int] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Идентификаторы преподавателей для удаления",
    )


class CourseTeacherRead(BaseModel):
    id: int
    course_id: int
    user_id: int
    added_by_user_id: int | None
    created_at: datetime
    updated_at: datetime


class CourseTeacherListItem(BaseModel):
    id: int
    course_id: int
    user_id: int
    created_at: datetime
