"""Тесты InviteRefCourseService (инвайт-ссылки курсов)"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.endpoints.courses.invites.service import (
    invites_service,
)
from backend.models import Course, CourseMembership, User


async def _create_user(db_session: AsyncSession, email: str = "t@t.com") -> User:
    u = User(email=email, password_hash="h", first_name="A", last_name="B")
    db_session.add(u)
    await db_session.commit()
    return u


async def _create_course(db_session: AsyncSession, user: User) -> Course:
    from backend.api.endpoints.courses.service import course_service

    return await course_service.create_course(
        author_id=user.id,
        title="Test",
        description="Test course description",
        session=db_session,
    )


@pytest.mark.asyncio
async def test_create_invite_generates_token(db_session: AsyncSession):
    u = await _create_user(db_session)
    course = await _create_course(db_session, u)

    invite = await invites_service.create_invite_ref(
        course_id=course.id,
        creator_id=u.id,
        max_uses=None,
        expires_at=None,
        session=db_session,
    )
    assert invite.token
    assert len(invite.token) == 43  # token_urlsafe(32) = 43 символа


@pytest.mark.asyncio
async def test_get_invite_by_course(db_session: AsyncSession):
    u = await _create_user(db_session)
    course = await _create_course(db_session, u)

    await invites_service.create_invite_ref(course.id, u.id, None, None, db_session)
    found = await invites_service.get_invite_ref_by_course_id(course.id, db_session)
    assert found.course_id == course.id


@pytest.mark.asyncio
async def test_join_by_invite_creates_membership(db_session: AsyncSession):
    owner = await _create_user(db_session, "owner@t.com")
    student = await _create_user(db_session, "student@t.com")
    course = await _create_course(db_session, owner)

    invite = await invites_service.create_invite_ref(
        course.id, owner.id, None, None, db_session
    )

    await invites_service.join_by_invites_ref(
        user_id=student.id,
        token=invite.token,
        session=db_session,
    )

    from sqlalchemy import select

    stmt = select(CourseMembership).where(
        CourseMembership.course_id == course.id,
        CourseMembership.user_id == student.id,
    )
    result = await db_session.execute(stmt)
    assert result.scalar() is not None


@pytest.mark.asyncio
async def test_join_deactivated_invite_raises_410(db_session: AsyncSession):
    owner = await _create_user(db_session, "owner@t.com")
    student = await _create_user(db_session, "s@t.com")
    course = await _create_course(db_session, owner)

    invite = await invites_service.create_invite_ref(
        course.id, owner.id, None, None, db_session
    )
    await invites_service.update_invite_ref(
        invite, is_active=False, max_uses=None, expires_at=None, session=db_session
    )

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await invites_service.join_by_invites_ref(student.id, invite.token, db_session)
    assert exc.value.status_code == 410


@pytest.mark.asyncio
async def test_delete_invite(db_session: AsyncSession):
    u = await _create_user(db_session)
    course = await _create_course(db_session, u)

    invite = await invites_service.create_invite_ref(
        course.id, u.id, None, None, db_session
    )
    await invites_service.delete_invite_ref(invite, db_session)

    from fastapi import HTTPException

    with pytest.raises(HTTPException):
        await invites_service.get_invite_ref(invite.token, db_session)
