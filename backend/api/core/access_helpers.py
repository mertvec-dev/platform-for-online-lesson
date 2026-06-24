"""Вспомогательные проверки доступа, общие для всех доменов"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ...models import Lesson, Room, RoomMembership, RoomTeacher
from .database import db


async def _room_membership_exists(
    session: AsyncSession,
    room_id: int,
    user_id: int,
) -> bool:
    """Проверяет, есть ли у пользователя активное участие в комнате"""
    statement = select(RoomMembership).where(
        RoomMembership.room_id == room_id,
        RoomMembership.user_id == user_id,
        RoomMembership.is_active,
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none() is not None


async def _room_teacher_assignment_exists(
    session: AsyncSession,
    room_id: int,
    user_id: int,
) -> bool:
    """Проверяет, назначен ли пользователь преподавателем комнаты"""
    statement = select(RoomTeacher).where(
        RoomTeacher.room_id == room_id,
        RoomTeacher.user_id == user_id,
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none() is not None


async def get_room_or_404(
    room_id: int,
    session: AsyncSession = Depends(db.get_session),
) -> Room:
    """Возвращает комнату по `room_id` или выбрасывает 404"""
    statement = select(Room).where(Room.id == room_id)
    result = await session.execute(statement)
    room = result.scalar_one_or_none()

    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Комната не найдена",
        )

    return room


async def get_lesson_or_404(
    lesson_id: int,
    session: AsyncSession = Depends(db.get_session),
) -> Lesson:
    """Возвращает урок по `lesson_id` или выбрасывает 404"""
    statement = select(Lesson).where(Lesson.id == lesson_id)
    result = await session.execute(statement)
    lesson = result.scalar_one_or_none()

    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Урок не найден",
        )

    return lesson


async def _get_room_of_lesson(
    session: AsyncSession,
    lesson: Lesson,
) -> Room:
    """Возвращает комнату урока или выбрасывает 404"""
    statement = select(Room).where(Room.id == lesson.room_id)
    result = await session.execute(statement)
    room = result.scalar_one_or_none()

    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Комната урока не найдена",
        )

    return room
