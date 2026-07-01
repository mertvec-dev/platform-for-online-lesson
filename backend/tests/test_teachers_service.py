"""Тесты TeacherService"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.endpoints.courses.teachers.service import (
    teacher_service,
)
from backend.models import User


async def _create_user(db_session: AsyncSession, email: str = "t@t.com") -> User:
    u = User(email=email, password_hash="h", first_name="A", last_name="B")
    db_session.add(u)
    await db_session.commit()
    return u


async def _create_course(db_session: AsyncSession, user: User):
    from backend.api.endpoints.courses.service import course_service

    return await course_service.create_course(
        author_id=user.id,
        title="Test",
        description="Test course description",
        session=db_session,
    )


@pytest.mark.asyncio
async def test_add_teachers(db_session: AsyncSession):
    owner = await _create_user(db_session, "owner@t.com")
    teacher = await _create_user(db_session, "teacher@t.com")
    course = await _create_course(db_session, owner)

    teachers = await teacher_service.add_teachers(
        course.id,
        [teacher.id],
        added_by_user_id=owner.id,
        session=db_session,
    )
    assert len(teachers) == 1
    assert teachers[0].user_id == teacher.id


@pytest.mark.asyncio
async def test_list_teachers(db_session: AsyncSession):
    owner = await _create_user(db_session)
    teacher1 = await _create_user(db_session, "t1@t.com")
    teacher2 = await _create_user(db_session, "t2@t.com")
    course = await _create_course(db_session, owner)

    await teacher_service.add_teachers(
        course.id, [teacher1.id, teacher2.id], owner.id, db_session
    )

    result = await teacher_service.list_teachers(course.id, db_session)
    assert len(result) == 2


@pytest.mark.asyncio
async def test_remove_teachers(db_session: AsyncSession):
    owner = await _create_user(db_session, "owner@t.com")
    teacher = await _create_user(db_session, "teacher@t.com")
    course = await _create_course(db_session, owner)

    await teacher_service.add_teachers(course.id, [teacher.id], owner.id, db_session)
    await teacher_service.remove_teachers(course.id, [teacher.id], db_session)

    result = await teacher_service.list_teachers(course.id, db_session)
    assert len(result) == 0
