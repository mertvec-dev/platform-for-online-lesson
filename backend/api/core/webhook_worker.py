"""Накопление webhook-событий в Redis-буфере и батчевая запись в БД."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, UTC

from sqlalchemy import select as sa_select

from backend.api.core.config import settings
from backend.api.core.database import Database
from backend.api.core.redis import redis_client
from backend.api.core.redis_keys import WEBHOOK_BUFFER, WEBHOOK_FLUSH_INTERVAL
from backend.models.lessons import Lesson, LessonStatus
from backend.models.lessons_logs import LessonLog

logger = logging.getLogger(__name__)


class WebhookBufferWorker:
    def __init__(self) -> None:
        self._db: Database | None = None
        self._task: asyncio.Task | None = None

    def connect_db(self, db: Database) -> None:
        self._db = db

    async def start(self) -> None:
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        try:
            await self._flush()
        except Exception:
            logger.exception("Финальный флаш буфера при остановке провален")

    async def flush_now(self) -> None:
        try:
            await self._flush()
        except Exception:
            logger.exception("Принудительный флаш буфера провален")

    async def push(self, payload: dict) -> None:
        try:
            await redis_client.get_client().lpush(WEBHOOK_BUFFER, json.dumps(payload))
        except Exception:
            logger.exception("Не удалось поместить событие в буфер")

    async def _loop(self) -> None:
        while True:
            await asyncio.sleep(WEBHOOK_FLUSH_INTERVAL)
            try:
                await self._flush()
            except Exception:
                logger.exception("Периодический флаш буфера провален")
            try:
                await self._cleanup_stale_lessons()
            except Exception:
                logger.exception("Зачистка зависших уроков провалена")

    async def _flush(self) -> None:
        if self._db is None:
            return

        client = redis_client.get_client()
        length = await client.llen(WEBHOOK_BUFFER)
        if length == 0:
            return

        pipe = client.pipeline()
        pipe.lrange(WEBHOOK_BUFFER, 0, -1)
        pipe.delete(WEBHOOK_BUFFER)
        raw_items, _ = await pipe.execute()

        if not raw_items:
            return

        events: list[dict] = []
        for item in raw_items:
            try:
                events.append(json.loads(item))
            except json.JSONDecodeError:
                continue

        if not events:
            return

        logger.info("Флаш %d webhook-событий из буфера", len(events))

        joins = [e for e in events if e.get("event") == "participant_joined"]
        leaves = [e for e in events if e.get("event") == "participant_left"]

        async with self._db.session() as session:
            if joins:
                logs_to_insert = [
                    LessonLog(
                        lesson_id=j["lesson_id"],
                        user_id=j["user_id"],
                        session_id=j.get("session_id"),
                        joined_at=_parse_ts(j.get("joined_at")),
                        webhook_received_at=datetime.now(UTC),
                    )
                    for j in joins
                ]
                session.add_all(logs_to_insert)
                await session.flush()

            if leaves:
                for lv in leaves:
                    log = await _find_open_log(session, lv)
                    if log is not None:
                        log.left_at = _parse_ts(lv.get("left_at"))
                        log.duration_seconds = int(
                            (log.left_at - log.joined_at).total_seconds()
                        )
                        log.webhook_received_at = datetime.now(UTC)

            await session.commit()

    async def _cleanup_stale_lessons(self) -> None:
        """Принудительно завершает уроки, висящие в RUNNING дольше планового времени."""
        if self._db is None:
            return

        buffer = timedelta(minutes=settings.LESSON_MAX_DURATION_MINUTES)

        async with self._db.session() as session:
            stmt = sa_select(Lesson).where(
                Lesson.status == LessonStatus.RUNNING,
                Lesson.started_at.is_not(None),
            )
            result = await session.execute(stmt)
            running_lessons = result.scalars().all()

            now = datetime.now(UTC)
            stale = [
                lesson
                for lesson in running_lessons
                if lesson.scheduled_at + timedelta(minutes=lesson.duration_minutes) + buffer < now
            ]

            if not stale:
                return

            from backend.api.core.egress_service import egress_service

            for lesson in stale:
                logger.warning(
                    "Урок %d висит в RUNNING с %s (план: %s + %d мин), принудительно завершаем",
                    lesson.id, lesson.started_at, lesson.scheduled_at, lesson.duration_minutes,
                )
                if lesson.egress_id:
                    await egress_service.stop_recording(lesson.egress_id)
                    # egress_id не сбрасываем — egress_ended вебхук использует его
                lesson.status = LessonStatus.ENDED
                lesson.ended_at = now

            await session.commit()
            logger.info("Зачищено %d зависших уроков", len(stale))


async def _find_open_log(session, lv: dict) -> LessonLog | None:
    lesson_id = lv["lesson_id"]
    user_id = lv["user_id"]
    session_id = lv.get("session_id")

    if session_id:
        stmt = sa_select(LessonLog).where(
            LessonLog.lesson_id == lesson_id,
            LessonLog.user_id == user_id,
            LessonLog.session_id == session_id,
            LessonLog.left_at.is_(None),
        )
        result = await session.execute(stmt)
        log = result.scalar_one_or_none()
        if log is not None:
            return log

    stmt = (
        sa_select(LessonLog)
        .where(
            LessonLog.lesson_id == lesson_id,
            LessonLog.user_id == user_id,
            LessonLog.left_at.is_(None),
        )
        .order_by(LessonLog.joined_at.desc())
    )
    result = await session.execute(stmt)
    return result.scalars().first()


def _parse_ts(val: str | None) -> datetime:
    if not val:
        return datetime.now(UTC)
    try:
        return datetime.fromisoformat(val)
    except ValueError:
        return datetime.now(UTC)


worker = WebhookBufferWorker()
