"""Роуты для управления уроками"""

import logging

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from .....models import Course, Lesson, User
from ....core import ApiResponse, LiveKitService, db
from ....core.config import settings
from ....core.pagination import DEFAULT_PAGE_SIZE
from ...auth.dependencies import get_current_user
from ...lessons_logs.schemas import LessonLogListItem
from ...lessons_logs.service import lesson_log_service
from ..dependencies import (
    ensure_course_member_or_admin_by_slug,
    ensure_course_teacher_or_admin_by_slug,
)
from .dependencies import (
    ensure_lesson_course_member_or_admin,
    ensure_lesson_teacher_or_admin,
)
from .schemas import (
    CreateLesson,
    EndLessonRequest,
    LessonListItem,
    LessonRead,
    StartLessonRequest,
    UpdateLesson,
)
from .service import lesson_service

lesson_router = APIRouter(tags=["course-lessons"])
livekit = LiveKitService()

logger = logging.getLogger(__name__)


@lesson_router.post(
    "/{slug}/lessons",
    summary="Создать урок",
    response_model=ApiResponse[LessonRead],
)
async def create_lesson(
    body: CreateLesson,
    course: Course = Depends(ensure_course_teacher_or_admin_by_slug),
    session: AsyncSession = Depends(db.get_session),
):
    logger.info("POST /courses/%s/lessons — создание урока", course.slug)
    lesson = await lesson_service.create_lesson(
        course_id=course.id,
        title=body.title,
        description=body.description,
        max_participants=body.max_participants,
        scheduled_at=body.scheduled_at,
        session=session,
    )
    return ApiResponse.ok(
        data=lesson,
        message="Урок создан",
        status_code=status.HTTP_201_CREATED,
    )


@lesson_router.get(
    "/{slug}/lessons",
    summary="Список уроков курса",
    response_model=ApiResponse[list[LessonListItem]],
)
async def get_lessons(
    course: Course = Depends(ensure_course_member_or_admin_by_slug),
    session: AsyncSession = Depends(db.get_session),
    limit: int = DEFAULT_PAGE_SIZE,
    offset: int = 0,
):
    logger.info("GET /courses/%s/lessons — запрос списка уроков", course.slug)
    lessons = await lesson_service.get_lessons(
        course.id, session, limit=limit, offset=offset
    )
    return ApiResponse.ok(data=lessons, message="Список уроков")


@lesson_router.get(
    "/{slug}/lessons/{lesson_id}",
    summary="Получить урок",
    response_model=ApiResponse[LessonRead],
)
async def get_lesson(
    lesson: Lesson = Depends(ensure_lesson_course_member_or_admin),  # type: ignore[arg-type]
):
    logger.info("GET /courses/{slug}/lessons/%d — запрос урока", lesson.id)
    return ApiResponse.ok(data=lesson, message="Урок найден")


@lesson_router.patch(
    "/{slug}/lessons/{lesson_id}",
    summary="Обновить урок",
    response_model=ApiResponse[LessonRead],
)
async def update_lesson(
    body: UpdateLesson,
    lesson: Lesson = Depends(ensure_lesson_teacher_or_admin),  # type: ignore[arg-type]
    session: AsyncSession = Depends(db.get_session),
):
    logger.info("PATCH /courses/{slug}/lessons/%d — обновление урока", lesson.id)
    lesson = await lesson_service.update_lesson(
        lesson=lesson,
        title=body.title,
        description=body.description,
        max_participants=body.max_participants,
        scheduled_at=body.scheduled_at,
        session=session,
    )
    return ApiResponse.ok(data=lesson, message="Урок обновлён")


@lesson_router.post(
    "/{slug}/lessons/{lesson_id}/start",
    summary="Начать урок",
    response_model=ApiResponse[LessonRead],
)
async def start_lesson(
    body: StartLessonRequest,
    lesson: Lesson = Depends(ensure_lesson_teacher_or_admin),  # type: ignore[arg-type]
    session: AsyncSession = Depends(db.get_session),
):
    logger.info("POST /courses/{slug}/lessons/%d/start — начало урока", lesson.id)
    lesson = await lesson_service.start_lesson(
        lesson=lesson,
        started_at=body.started_at,
        session=session,
    )
    return ApiResponse.ok(data=lesson, message="Урок начат")


@lesson_router.post(
    "/{slug}/lessons/{lesson_id}/end",
    summary="Завершить урок",
    response_model=ApiResponse[LessonRead],
)
async def end_lesson(
    body: EndLessonRequest,
    lesson: Lesson = Depends(ensure_lesson_teacher_or_admin),  # type: ignore[arg-type]
    session: AsyncSession = Depends(db.get_session),
):
    logger.info("POST /courses/{slug}/lessons/%d/end — завершение урока", lesson.id)
    lesson = await lesson_service.end_lesson(
        lesson=lesson,
        ended_at=body.ended_at,
        session=session,
    )
    return ApiResponse.ok(data=lesson, message="Урок завершён")


@lesson_router.delete(
    "/{slug}/lessons/{lesson_id}",
    summary="Удалить урок",
    response_model=ApiResponse[None],
)
async def delete_lesson(
    lesson: Lesson = Depends(ensure_lesson_teacher_or_admin),  # type: ignore[arg-type]
    session: AsyncSession = Depends(db.get_session),
):
    logger.info("DELETE /courses/{slug}/lessons/%d — удаление урока", lesson.id)
    await lesson_service.delete_lesson(lesson, session)
    return ApiResponse.ok(data=None, message="Урок удалён")


class LiveKitTokenResponse(BaseModel):
    token: str
    room_name: str
    ws_url: str


@lesson_router.get(
    "/{slug}/lessons/{lesson_id}/token",
    summary="Получить LiveKit-токен для подключения к уроку",
    response_model=ApiResponse[LiveKitTokenResponse],
)
async def get_livekit_token(
    lesson: Lesson = Depends(ensure_lesson_course_member_or_admin),  # type: ignore[arg-type]
    current_user: User = Depends(get_current_user),
):
    logger.info(
        "GET /courses/{slug}/lessons/%d/token — запрос LiveKit-токена пользователем %d",
        lesson.id,
        current_user.id,
    )
    room = livekit.room_name(lesson.course_id, lesson.id)
    token = livekit.generate_token(
        room_name=room,
        participant_id=str(current_user.id),
        participant_name=f"{current_user.first_name} {current_user.last_name}",
    )
    return ApiResponse.ok(
        data=LiveKitTokenResponse(
            token=token,
            room_name=room,
            ws_url=settings.LIVEKIT_WS_URL,
        ),
        message="Токен сгенерирован",
    )


@lesson_router.get(
    "/{slug}/lessons/{lesson_id}/logs",
    summary="Логи посещения урока",
    response_model=ApiResponse[list[LessonLogListItem]],
)
async def get_lesson_logs(
    lesson: Lesson = Depends(ensure_lesson_teacher_or_admin),  # type: ignore[arg-type]
    session: AsyncSession = Depends(db.get_session),
):
    logger.info("GET /courses/{slug}/lessons/%d/logs — запрос логов", lesson.id)
    logs = await lesson_log_service.get_logs_for_lesson(lesson.id, session)
    return ApiResponse.ok(data=logs, message="Логи посещения")
