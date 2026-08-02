"""Эндпоинты LiveKit: webhook-обработчик событий с проверкой подписи."""

import hashlib
import hmac
import json
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Header, Request
from starlette.responses import Response

from backend.api.core.config import settings
from backend.api.core.redis import redis_client
from backend.api.core.redis_keys import (
    WEBHOOK_IP_LIMIT,
    WEBHOOK_IP_WINDOW,
    ratelimit_webhook_ip_key,
)
from backend.api.core.webhook_worker import worker
from backend.api.endpoints.lessons_logs.service import parse_room_name

logger = logging.getLogger(__name__)

livekit_webhook_router = APIRouter(prefix="/livekit", tags=["livekit-webhooks"])


def _verify_signature(body: bytes, authorization: str | None) -> bool:
    """Проверяет SHA-256 подпись LiveKit-вебхука."""
    if not authorization:
        return False

    expected = hmac.new(
        settings.LIVEKIT_API_KEY.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, authorization)


def _client_ip(request: Request) -> str:
    """Извлекает IP клиента, учитывая X-Forwarded-For."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@livekit_webhook_router.post(
    "/webhook",
    summary="Webhook-обработчик событий LiveKit",
)
async def livekit_webhook(
    request: Request,
    authorization: str | None = Header(default=None),
) -> Response:
    # Rate-limit: защита от флуда до проверки подписи
    ip = _client_ip(request)
    count = await redis_client.incr_with_ttl(
        ratelimit_webhook_ip_key(ip), WEBHOOK_IP_WINDOW
    )
    if count > WEBHOOK_IP_LIMIT:
        logger.warning("Webhook: слишком много запросов с IP %s, отбрасываем", ip)
        return Response(status_code=429)

    body = await request.body()

    if not _verify_signature(body, authorization):
        logger.warning("Webhook: недействительная подпись")
        return Response(status_code=401)

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        logger.warning("Webhook: тело запроса не является JSON")
        return Response(status_code=400)

    event = payload.get("event", "unknown")
    room = payload.get("room", {})
    room_name = room.get("name", "")
    participant = payload.get("participant", {})
    participant_id = participant.get("identity", "")

    logger.info(
        "Webhook: %s, комната: %s, участник: %s",
        event,
        room_name,
        participant_id,
    )

    if event in ("participant_joined", "participant_left"):
        parsed = parse_room_name(room_name)
        if parsed is None:
            logger.debug(
                "Webhook: комната '%s' не соответствует шаблону course_X_lesson_Y",
                room_name,
            )
            return Response(status_code=200)

        _course_id, lesson_id = parsed

        try:
            user_id = int(participant_id)
        except (ValueError, TypeError):
            logger.warning(
                "Webhook: нечисловой participant_id '%s', пропускаем",
                participant_id,
            )
            return Response(status_code=200)

        ts = _parse_timestamp(payload.get("created_at") or payload.get("timestamp"))
        session_id = payload.get("id") or None
        ts_field = "joined_at" if event == "participant_joined" else "left_at"

        await worker.push(
            {
                "event": event,
                "lesson_id": lesson_id,
                "user_id": user_id,
                "session_id": session_id,
                ts_field: ts.isoformat(),
            }
        )

    elif event == "room_finished":
        parsed = parse_room_name(room_name)
        if parsed is not None:
            _course_id, lesson_id = parsed
            await _finish_lesson_on_room_finished(lesson_id)

        try:
            await worker.flush_now()
        except Exception:
            logger.exception(
                "Принудительный флаш буфера при завершении комнаты провален"
            )

    elif event == "egress_ended":
        egress_id = payload.get("egress_id", "")
        file_path = payload.get("output", {}).get("location", "")
        await _save_recording_url(egress_id, file_path)

    return Response(status_code=200)


def _parse_timestamp(raw: str | None) -> datetime:
    if not raw:
        return datetime.now(UTC)
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return datetime.now(UTC)


async def _save_recording_url(egress_id: str, file_path: str) -> None:
    """Сохраняет URL записи в урок по egress_id."""
    if not egress_id or not file_path:
        logger.warning("egress_ended: пустой egress_id или file_path")
        return

    try:
        from sqlalchemy import update

        from backend.api.core.database import db
        from backend.models.lessons import Lesson

        async with db.session() as session:
            stmt = (
                update(Lesson)
                .where(Lesson.egress_id == egress_id)
                .values(recording_url=file_path)
            )
            await session.execute(stmt)
            await session.commit()
            logger.info("Запись сохранена: egress_id=%s, path=%s", egress_id, file_path)
    except Exception:
        logger.exception("Ошибка сохранения recording_url для egress_id=%s", egress_id)


async def _finish_lesson_on_room_finished(lesson_id: int) -> None:
    """Останавливает Egress и завершает урок при room_finished (препод закрыл вкладку)."""
    try:
        from backend.api.core.database import db
        from backend.api.core.egress_service import egress_service
        from backend.models.lessons import Lesson, LessonStatus

        async with db.session() as session:
            lesson = await session.get(Lesson, lesson_id)
            if lesson is None:
                return
            if lesson.status != LessonStatus.RUNNING:
                return  # уже завершён через end_lesson

            if lesson.egress_id:
                await egress_service.stop_recording(lesson.egress_id)
                # egress_id НЕ сбрасываем — egress_ended вебхук использует его
                # для поиска урока при сохранении recording_url

            lesson.status = LessonStatus.ENDED
            lesson.ended_at = datetime.now(UTC)
            await session.commit()
            logger.info("Урок %d завершён по room_finished", lesson_id)
    except Exception:
        logger.exception("Ошибка завершения урока %d по room_finished", lesson_id)
