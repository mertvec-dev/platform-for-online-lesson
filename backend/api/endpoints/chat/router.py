"""WebSocket эндпоинт чата (только во время занятия)"""

import logging

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from ...core import db, websocket_manager
from ...core.access_helpers import _course_membership_exists
from ..auth.ws_auth import get_user_id_from_cookie
from .schemas import CreateChatMessage
from .service import chat_message_service

ws_router = APIRouter(prefix="/ws/chat", tags=["ws_chat"])

logger = logging.getLogger(__name__)


@ws_router.websocket("{course_id}")
async def ws_chat(
    websocket: WebSocket,
    course_id: int,
    user_id: int = Depends(get_user_id_from_cookie),
):
    """
    WebSocket для чата комнаты во время занятия.

    Аутентификация — через httponly куку access_token.
    Сообщения валидируются, сохраняются в БД и рассылаются через Redis.

    Доступ — только участникам комнаты.
    """
    logger.info(
        "WS /ws/chat/%d — подключение к чату курса, пользователь %d", course_id, user_id
    )
    async with db.session() as session:
        if not await _course_membership_exists(session, course_id, user_id):
            await websocket.close(code=4003)
            return

    await websocket_manager.connect(websocket, user_id, course_id)

    try:
        while True:
            try:
                raw = await websocket.receive_text()
            except WebSocketDisconnect:
                break
            if not raw.strip():
                continue

            try:
                msg = CreateChatMessage.model_validate_json(raw)
            except ValidationError:
                await websocket.send_json(
                    {
                        "error": (
                            "Невалидное сообщение. "
                            "Ожидаются поля: course_id (int), text (str, 1-500)"
                        )
                    }
                )
                continue

            async with db.session() as session:
                saved = await chat_message_service.save(
                    course_id=course_id,
                    author_id=user_id,
                    text=msg.text,
                    db=session,
                )

            payload = {
                "id": saved.id,
                "course_id": course_id,
                "author_id": user_id,
                "text": msg.text,
                "created_at": saved.created_at.isoformat(),
                "sender_id": user_id,
            }
            await websocket_manager.broadcast(course_id, payload)
    finally:
        websocket_manager.disconnect(user_id, course_id)
