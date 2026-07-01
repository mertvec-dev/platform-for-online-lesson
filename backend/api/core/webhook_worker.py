"""Накопление webhook-событий в Redis-буфере и батчевая запись в БД."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select as sa_select

from backend.api.core.database import Database
from backend.api.core.redis import redis_client
from backend.api.core.redis_keys import WEBHOOK_BUFFER, WEBHOOK_FLUSH_INTERVAL
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
                        webhook_received_at=datetime.now(timezone.utc),
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
                        log.webhook_received_at = datetime.now(timezone.utc)

            await session.commit()


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
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(val.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


worker = WebhookBufferWorker()
