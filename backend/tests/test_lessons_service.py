"""Тесты LessonService"""

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.endpoints.courses.lessons.service import lesson_service
from backend.models import User
from backend.models.lessons import LessonStatus

service = lesson_service


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
async def test_create_lesson(db_session: AsyncSession):
    u = await _create_user(db_session)
    course = await _create_course(db_session, u)

    lesson = await service.create_lesson(
        course_id=course.id,
        title="Урок 1",
        description="Описание урока один",
        max_participants=30,
        scheduled_at=datetime(2026, 7, 10, 12, 0, tzinfo=UTC),
        duration_minutes=90,
        session=db_session,
    )
    assert lesson.status == LessonStatus.SCHEDULED
    assert lesson.title == "Урок 1"
    assert lesson.duration_minutes == 90


@pytest.mark.asyncio
async def test_start_lesson(db_session: AsyncSession):
    u = await _create_user(db_session)
    course = await _create_course(db_session, u)

    lesson = await service.create_lesson(
        course.id,
        "Урок",
        "Описание урока один",
        30,
        datetime(2026, 7, 10, 12, 0, tzinfo=UTC),
        60,
        db_session,
    )
    started = await service.start_lesson(lesson, None, db_session)
    assert started.status == LessonStatus.RUNNING
    assert started.started_at is not None


@pytest.mark.asyncio
async def test_end_lesson(db_session: AsyncSession):
    u = await _create_user(db_session)
    course = await _create_course(db_session, u)

    lesson = await service.create_lesson(
        course.id,
        "Урок",
        "Описание урока один",
        30,
        datetime(2026, 7, 10, 12, 0, tzinfo=UTC),
        60,
        db_session,
    )
    await service.start_lesson(lesson, None, db_session)
    ended = await service.end_lesson(lesson, None, db_session)
    assert ended.status == LessonStatus.ENDED
    assert ended.ended_at is not None


@pytest.mark.asyncio
async def test_cannot_start_ended_lesson(db_session: AsyncSession):
    u = await _create_user(db_session)
    course = await _create_course(db_session, u)

    lesson = await service.create_lesson(
        course.id,
        "Урок",
        "Описание урока один",
        30,
        datetime(2026, 7, 10, 12, 0, tzinfo=UTC),
        60,
        db_session,
    )
    await service.start_lesson(lesson, None, db_session)
    await service.end_lesson(lesson, None, db_session)

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await service.start_lesson(lesson, None, db_session)
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_update_lesson_changes_title(db_session: AsyncSession):
    u = await _create_user(db_session)
    course = await _create_course(db_session, u)

    lesson = await service.create_lesson(
        course.id,
        "Старый заголовок",
        "Описание урока один",
        30,
        datetime(2026, 7, 10, 12, 0, tzinfo=UTC),
        60,
        db_session,
    )
    updated = await service.update_lesson(
        lesson,
        "Новый заголовок",
        None,
        None,
        None,
        None,
        db_session,
    )
    assert updated.title == "Новый заголовок"


@pytest.mark.asyncio
async def test_delete_lesson(db_session: AsyncSession):
    u = await _create_user(db_session)
    course = await _create_course(db_session, u)

    lesson = await service.create_lesson(
        course.id,
        "Урок",
        "Описание урока один",
        30,
        datetime(2026, 7, 10, 12, 0, tzinfo=UTC),
        60,
        db_session,
    )
    await service.delete_lesson(lesson, db_session)

    found = await service.get_lesson(lesson.id, db_session)
    assert found is None
