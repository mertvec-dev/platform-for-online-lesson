"""Тесты UserService"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.endpoints.users.service import user_service
from backend.models import User
from backend.models.users import Role


async def _create_user(
    session: AsyncSession,
    email: str = "test@example.com",
    first_name: str = "John",
    last_name: str = "Doe",
    role: Role = Role.STUDENT,
) -> User:
    u = User(
        email=email,
        password_hash="hash",
        first_name=first_name,
        last_name=last_name,
        role=role,
        is_active=True,
    )
    session.add(u)
    await session.commit()
    return u


@pytest.mark.asyncio
async def test_get_user_returns_user(db_session: AsyncSession):
    u = await _create_user(db_session)
    found = await user_service.get_user(u.id, db_session)
    assert found.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_user_not_found_raises_404(db_session: AsyncSession):
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await user_service.get_user(99999, db_session)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_users_with_limit(db_session: AsyncSession):
    await _create_user(db_session, "a@a.com")
    await _create_user(db_session, "b@b.com")
    await _create_user(db_session, "c@c.com")

    users = await user_service.get_users(db_session, limit=2, offset=0)
    assert len(users) == 2


@pytest.mark.asyncio
async def test_update_user_changes_fields(db_session: AsyncSession):
    u = await _create_user(db_session)
    updated = await user_service.update_user(
        u,
        first_name="Jane",
        last_name=None,
        email=None,
        role=None,
        is_active=None,
        session=db_session,
    )
    assert updated.first_name == "Jane"
    assert updated.last_name == "Doe"  # не изменилось


@pytest.mark.asyncio
async def test_update_user_role_by_admin(db_session: AsyncSession):
    u = await _create_user(db_session)
    updated = await user_service.update_user(
        u,
        first_name=None,
        last_name=None,
        email=None,
        role=Role.TEACHER,
        is_active=None,
        session=db_session,
    )
    assert updated.role == Role.TEACHER


@pytest.mark.asyncio
async def test_set_users_active(db_session: AsyncSession):
    u1 = await _create_user(db_session, "a@a.com")
    u2 = await _create_user(db_session, "b@b.com")

    await user_service.set_users_active([u1.id, u2.id], False, db_session)

    u1_rel = await user_service.get_user(u1.id, db_session)
    u2_rel = await user_service.get_user(u2.id, db_session)
    assert u1_rel.is_active is False
    assert u2_rel.is_active is False


@pytest.mark.asyncio
async def test_delete_users(db_session: AsyncSession):
    u = await _create_user(db_session)
    await user_service.delete_users([u.id], db_session)

    from fastapi import HTTPException

    with pytest.raises(HTTPException):
        await user_service.get_user(u.id, db_session)
