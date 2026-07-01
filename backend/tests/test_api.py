"""Тесты API-эндпоинтов (без БД)"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_health_check(client: AsyncClient):
    resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "LIVE"


@pytest.mark.asyncio
async def test_courses_create_requires_auth(client: AsyncClient):
    resp = await client.post(
        "/courses/create",
        json={"title": "Test", "description": "Test course description"},
    )
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_auth_register_validation(client: AsyncClient):
    resp = await client.post(
        "/auth/register",
        json={
            "email": "not-an-email",
            "password": "123",
            "first_name": "A",
            "last_name": "B",
        },
    )
    assert resp.status_code == 422  # validation error


@pytest.mark.asyncio
async def test_users_me_requires_auth(client: AsyncClient):
    resp = await client.get("/users/me")
    assert resp.status_code == 401
