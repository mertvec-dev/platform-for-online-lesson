"""
WebSocket Connection Manager

Каждое подключение подписывается на Redis-канал комнаты.
Сообщения идут через Redis Pub/Sub — прозрачно между серверами.

Архитектура:
  connect    → subscribe на канал комнаты, запуск фонового слушателя
  broadcast  → publish в канал (Redis раздаёт всем подписчикам)
  disconnect → отмена слушателя, unsubscribe

Отправитель не получает своё же сообщение — фильтрация по sender_id.
"""

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket
from redis.asyncio.client import PubSub

from .redis import redis_pubsub
from .redis_keys import chat_channel

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        # (course_id, user_id) → WebSocket
        self._sockets: dict[tuple[int, int], WebSocket] = {}
        # (course_id, user_id) → asyncio.Task
        self._tasks: dict[tuple[int, int], asyncio.Task[None]] = {}

    @property
    def active_connections(self) -> int:
        return len(self._sockets)

    async def connect(self, websocket: WebSocket, user_id: int, course_id: int) -> None:
        """
        Подписывает сокет на Redis-канал комнаты и запускает слушатель.
        """
        await websocket.accept()
        key = (course_id, user_id)
        self._sockets[key] = websocket

        pubsub = await redis_pubsub.subscribe(chat_channel(course_id))
        task = asyncio.create_task(self._forward(websocket, pubsub, key))
        self._tasks[key] = task

    async def _forward(
        self, ws: WebSocket, pubsub: PubSub, key: tuple[int, int]
    ) -> None:
        """
        Слушает Redis-канал и пересылает сообщения в WebSocket.

        Сообщения от СВОЕГО ЖЕ user_id пропускает — отправитель не получает эхо.
        """
        course_id, user_id = key
        try:
            async for raw in redis_pubsub.listen(pubsub):
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                if msg.get("sender_id") == user_id:
                    continue
                try:
                    await ws.send_json(msg)
                except Exception:
                    break
        finally:
            await redis_pubsub.unsubscribe(pubsub)
            self._sockets.pop(key, None)
            self._tasks.pop(key, None)

    def disconnect(self, user_id: int, course_id: int) -> None:
        """
        Отменяет слушатель, закрывает сокет и удаляет из реестра.
        """
        key = (course_id, user_id)
        task = self._tasks.pop(key, None)
        if task:
            task.cancel()
        self._sockets.pop(key, None)

    async def shutdown(self) -> None:
        """
        Graceful shutdown: закрывает все активные WebSocket-соединения.

        Отправляет системное сообщение и закрывает с кодом 1001 (going away).
        Вызывается при остановке приложения.
        """
        if not self._sockets:
            return

        logger.info("Завершение %d активных WebSocket-соединений", len(self._sockets))

        shutdown_msg = json.dumps(
            {"type": "system", "text": "Сервер завершает работу. Соединение закрыто."}
        )

        for key, ws in list(self._sockets.items()):
            try:
                await ws.send_text(shutdown_msg)
                await ws.close(code=1001)
            except Exception:
                pass

            task = self._tasks.pop(key, None)
            if task:
                task.cancel()

        self._sockets.clear()

    async def broadcast(self, course_id: int, payload: dict[str, Any]) -> None:
        """
        Публикует сообщение в Redis-канал комнаты.
        """
        await redis_pubsub.publish(chat_channel(course_id), json.dumps(payload))


websocket_manager = ConnectionManager()
