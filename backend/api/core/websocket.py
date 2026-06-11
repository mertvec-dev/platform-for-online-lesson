"""
WebSocket Connection Manager (Pub/Sub)

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

from fastapi import WebSocket
from redis.asyncio.client import PubSub

from .redis import redis_pubsub
from .redis_keys import chat_channel


class ConnectionManager:
    def __init__(self):
        # (room_id, user_id) → WebSocket
        self._sockets: dict[tuple[int, int], WebSocket] = {}
        # (room_id, user_id) → asyncio.Task
        self._tasks: dict[tuple[int, int], asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, user_id: int, room_id: int):
        """
        Подписывает сокет на Redis-канал комнаты и запускает слушатель.
        """
        key = (room_id, user_id)
        self._sockets[key] = websocket

        pubsub = await redis_pubsub.subscribe(chat_channel(room_id))
        task = asyncio.create_task(self._forward(websocket, pubsub, key))
        self._tasks[key] = task

    async def _forward(self, ws: WebSocket, pubsub: PubSub, key: tuple[int, int]):
        """
        Слушает Redis-канал и пересылает сообщения в WebSocket.

        Сообщения от СВОЕГО ЖЕ user_id пропускает — отправитель не получает эхо.
        """
        room_id, user_id = key
        try:
            async for raw in redis_pubsub.listen(pubsub):
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                # Не шлём отправителю его же сообщение
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

    def disconnect(self, user_id: int, room_id: int):
        """
        Отменяет слушатель и удаляет сокет.
        """
        key = (room_id, user_id)
        task = self._tasks.pop(key, None)
        if task:
            task.cancel()
        self._sockets.pop(key, None)

    async def broadcast(self, room_id: int, message: str):
        """
        Публикует сообщение в Redis-канал комнаты.
        """
        await redis_pubsub.publish(chat_channel(room_id), message)


websocket_manager = ConnectionManager()
