"""Тесты TeacherInviteService"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.endpoints.auth.teacher_invites.service import (
    teacher_invite_service,
)
from backend.models import User


async def _create_user(db_session: AsyncSession, email: str = "admin@t.com") -> User:
    u = User(email=email, password_hash="h", first_name="A", last_name="B")
    db_session.add(u)
    await db_session.commit()
    return u


@pytest.mark.asyncio
async def test_create_teacher_invite(db_session: AsyncSession):
    admin = await _create_user(db_session)
    invite = await teacher_invite_service.create(
        created_by=admin.id,
        max_uses=5,
        expires_at=None,
        session=db_session,
    )
    assert invite.token
    assert len(invite.token) == 43
    assert invite.max_uses == 5
    assert invite.is_active is True


@pytest.mark.asyncio
async def test_validate_and_consume_token(db_session: AsyncSession):
    admin = await _create_user(db_session)
    invite = await teacher_invite_service.create(admin.id, 1, None, db_session)

    result = await teacher_invite_service.validate_and_consume(invite.token, db_session)
    assert result.is_active is True


@pytest.mark.asyncio
async def test_validate_deactivated_token_raises_410(db_session: AsyncSession):
    admin = await _create_user(db_session)
    invite = await teacher_invite_service.create(admin.id, 1, None, db_session)
    await teacher_invite_service.update(
        invite, is_active=False, max_uses=None, expires_at=None, session=db_session
    )

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await teacher_invite_service.validate_and_consume(invite.token, db_session)
    assert exc.value.status_code == 410


@pytest.mark.asyncio
async def test_list_all_invites(db_session: AsyncSession):
    admin = await _create_user(db_session)
    await teacher_invite_service.create(admin.id, 1, None, db_session)
    await teacher_invite_service.create(admin.id, 2, None, db_session)

    result = await teacher_invite_service.list_all(db_session)
    assert len(result) == 2


@pytest.mark.asyncio
async def test_delete_invite(db_session: AsyncSession):
    admin = await _create_user(db_session)
    invite = await teacher_invite_service.create(admin.id, 1, None, db_session)

    await teacher_invite_service.delete(invite, db_session)

    found = await teacher_invite_service.get_by_token(invite.token, db_session)
    assert found is None
