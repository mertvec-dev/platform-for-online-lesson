"""Тесты CoursesService"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.endpoints.courses.service import course_service
from backend.models import Course, CourseMembership, User


async def _create_course(
    session: AsyncSession,
    user: User,
    title: str = "Математика",
) -> Course:
    return await course_service.create_course(
        author_id=user.id,
        title=title,
        description="Описание курса математики",
        session=session,
    )


@pytest.mark.asyncio
async def test_create_course_generates_slug(db_session: AsyncSession):
    u = User(email="t@t.com", password_hash="h", first_name="A", last_name="B")
    db_session.add(u)
    await db_session.commit()

    course = await _create_course(db_session, u)
    assert course.slug
    assert len(course.slug) >= 1
    assert course.title == "Математика"


@pytest.mark.asyncio
async def test_create_course_adds_author_as_member(db_session: AsyncSession):
    u = User(email="t@t.com", password_hash="h", first_name="A", last_name="B")
    db_session.add(u)
    await db_session.commit()

    course = await _create_course(db_session, u)

    # Автор должен быть участником
    from sqlalchemy import select

    stmt = select(CourseMembership).where(
        CourseMembership.course_id == course.id,
        CourseMembership.user_id == u.id,
    )
    result = await db_session.execute(stmt)
    membership = result.scalar()
    assert membership is not None


@pytest.mark.asyncio
async def test_list_user_courses_returns_only_members_courses(db_session: AsyncSession):
    u1 = User(email="u1@t.com", password_hash="h", first_name="A", last_name="B")
    u2 = User(email="u2@t.com", password_hash="h", first_name="C", last_name="D")
    db_session.add_all([u1, u2])
    await db_session.commit()

    await _create_course(db_session, u2, "Физика")

    courses = await course_service.list_user_courses(u1.id, db_session)
    # u1 не создавал курс и не участник
    assert len(courses) == 0


@pytest.mark.asyncio
async def test_update_course_changes_title(db_session: AsyncSession):
    u = User(email="t@t.com", password_hash="h", first_name="A", last_name="B")
    db_session.add(u)
    await db_session.commit()

    course = await _create_course(db_session, u)
    old_slug = course.slug

    updated = await course_service.update_course(
        course,
        title="Физика",
        description=None,
        is_active=None,
        session=db_session,
    )
    assert updated.title == "Физика"
    # slug должен измениться при смене title
    assert updated.slug != old_slug


@pytest.mark.asyncio
async def test_delete_course(db_session: AsyncSession):
    u = User(email="t@t.com", password_hash="h", first_name="A", last_name="B")
    db_session.add(u)
    await db_session.commit()

    course = await _create_course(db_session, u)
    await course_service.delete_course(course, db_session)

    from sqlalchemy import select

    stmt = select(Course).where(Course.id == course.id)
    result = await db_session.execute(stmt)
    assert result.scalar() is None
