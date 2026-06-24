"""WebSocket эндпоинты чата"""

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from ..auth.ws_auth import get_user_id_from_cookie
from ...core import websocket_manager
from .schemas import CreateChatMessage

ws_router = APIRouter(prefix="/ws/chat", tags=["ws_chat"])


@ws_router.websocket("{room_id}")
async def ws_chat(
    websocket: WebSocket,
    room_id: int,
    user_id: int = Depends(get_user_id_from_cookie),
):
    """
    WebSocket для чата комнаты.

    Аутентификация — через httponly куку access_token (браузер отправляет автоматически).
    Сообщения валидируются через Pydantic-схему CreateChatMessage.
    """
    await websocket.accept()
    await websocket_manager.connect(websocket, user_id, room_id)

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
                        "error": "Невалидное сообщение. Ожидаются поля: room_id (int), text (str, 1-500)"
                    }
                )
                continue

            payload = {
                "room_id": msg.room_id,
                "text": msg.text,
                "sender_id": user_id,
            }
            await websocket_manager.broadcast(room_id, payload)
    finally:
        websocket_manager.disconnect(user_id, room_id)
