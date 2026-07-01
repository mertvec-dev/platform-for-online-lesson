"""Seed-данные: создаёт дефолтного админа при первом запуске."""

from bcrypt import gensalt, hashpw
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.core.config import settings
from backend.models.users import Role, User


async def seed_default_admin(session: AsyncSession) -> None:
    """Создаёт админа с почтой/паролем из .env, если админов ещё нет."""

    result = await session.execute(select(User).where(User.role == Role.ADMIN).limit(1))  # type: ignore[arg-type]
    if result.scalar() is not None:
        return

    admin = User(
        email=settings.DEFAULT_ADMIN_EMAIL,
        password_hash=hashpw(
            settings.DEFAULT_ADMIN_PASSWORD.encode(), gensalt()
        ).decode(),
        first_name="Admin",
        last_name="Default",
        role=Role.ADMIN,
        is_active=True,
    )
    session.add(admin)
    await session.commit()
