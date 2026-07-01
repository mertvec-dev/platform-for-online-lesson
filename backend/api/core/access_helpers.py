"""Вспомогательные проверки доступа, общие для всех доменов"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ...models import Course, CourseInvite, CourseMembership, CourseTeacher, Lesson
from .database import db


async def _course_membership_exists(
    session: AsyncSession,
    course_id: int,
    user_id: int,
) -> bool:
    """Проверяет, есть ли у пользователя активное участие в комнате"""
    statement = select(CourseMembership).where(
        CourseMembership.course_id == course_id,
        CourseMembership.user_id == user_id,
        CourseMembership.is_active,
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none() is not None


async def _course_teacher_assignment_exists(
    session: AsyncSession,
    course_id: int,
    user_id: int,
) -> bool:
    """Проверяет, назначен ли пользователь преподавателем комнаты"""
    statement = select(CourseTeacher).where(
        CourseTeacher.course_id == course_id,
        CourseTeacher.user_id == user_id,
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none() is not None


async def get_course_or_404(
    course_id: int,
    session: AsyncSession = Depends(db.get_session),
) -> Course:
    """Возвращает курс по `course_id` или выбрасывает 404"""
    statement = select(Course).where(Course.id == course_id)
    result = await session.execute(statement)
    course = result.scalar_one_or_none()

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Курс не найден",
        )

    return course


async def get_course_by_slug_or_404(
    slug: str,
    session: AsyncSession = Depends(db.get_session),
) -> Course:
    """Возвращает курс по `slug` или выбрасывает 404"""
    statement = select(Course).where(Course.slug == slug)
    result = await session.execute(statement)
    course = result.scalar_one_or_none()

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Курс не найден",
        )

    return course


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


async def _get_course_of_lesson(
    session: AsyncSession,
    lesson: Lesson,
) -> Course:
    """Возвращает курс урока или выбрасывает 404"""
    statement = select(Course).where(Course.id == lesson.course_id)
    result = await session.execute(statement)
    course = result.scalar_one_or_none()

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Курс урока не найден",
        )

    return course


async def get_invite_by_token_or_404(
    token: str,
    session: AsyncSession = Depends(db.get_session),
) -> CourseInvite:
    """Возвращает инвайт по токену или 404"""
    statement = select(CourseInvite).where(CourseInvite.token == token)
    result = await session.execute(statement)
    invite = result.scalar_one_or_none()
    if invite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Приглашение не найдено",
        )
    return invite
