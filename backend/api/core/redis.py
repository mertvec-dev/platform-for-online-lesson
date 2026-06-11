"""Конфигурация Redis"""

from typing import Any, Optional, cast

import redis.asyncio as redis
from redis.asyncio.client import PubSub

from ...config import settings


class RedisClient:
    """
    Клиент Redis для обычных операций (кэш, rate-limiting, всякие счетчики)
    """

    def __init__(self):
        self._client: Optional[redis.Redis] = None

    def connect(self) -> None:
        self._client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
        )

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None

    def get_client(self) -> redis.Redis:
        if not self._client:
            raise RuntimeError("Redis не инициализирован")
        return self._client

    # === Методы кэша ===

    async def set_cache(
        self, key: str, value: Any, expire: Optional[int] = None
    ) -> None:
        """
        Устанавливает значение в кэш с опциональным TTL
        """
        local_client = self.get_client()
        if expire:
            await local_client.set(key, value, ex=expire)
        else:
            await local_client.set(key, value)

    async def get_cache(self, key: str) -> Optional[str]:
        """
        Возвращает значение из кэша по ключу
        """
        local_client = self.get_client()
        return cast(Optional[str], await local_client.get(key))

    async def delete_cache(self, key: str) -> None:
        """
        Удаляет значение из кэша по ключу
        """
        local_client = self.get_client()
        await local_client.delete(key)

    # === rate-limiting ===

    async def incr_with_ttl(self, key: str, ttl: int) -> int:
        """
        Совершает инкремент счетчика и устанавливает TTL для ключа

        Возвращает новое значение
        """
        _client = self.get_client()

        pipe = _client.pipeline()
        pipe.incr(key)
        pipe.expire(key, ttl)
        result = await pipe.execute()
        return result[0]

    async def is_rate_limited(
        self, key: str, limit: int, window: int, scope: str = "default"
    ) -> bool:
        """
        Проверяет, превышен ли лимит запросов для заданного ключа

        `scope` — спецификатор для разделения счетчиков,
        чтобы разные операции не пересекались по ключам.
        """
        key = f"{key}:{scope}"
        count = await self.incr_with_ttl(key, window)
        return count > limit


class RedisPubSub:
    """
    Redis Pub/Sub клиент для совершения подписки на каналы и публикации сообщений
    """

    def __init__(self, redis_client: RedisClient):
        self.redis_client = redis_client
        self.pubsub: Optional[PubSub] = None

    def get_client(self) -> redis.Redis:
        return self.redis_client.get_client()

    # === Pub/Sub методы ===

    async def publish(self, channel: str, message: str) -> int:
        """Публикация сообщения в канал"""
        _client = self.get_client()
        return await _client.publish(channel, message)

    async def subscribe(self, channel: str) -> PubSub:
        """Подписка на канал (возвращает pubsub объект)"""
        _client = self.get_client()
        pubsub = _client.pubsub()
        await pubsub.subscribe(channel)
        return pubsub

    async def unsubscribe(self, pubsub: PubSub, channel: Optional[str] = None) -> None:
        """Отписка от канала"""
        if channel:
            await pubsub.unsubscribe(channel)
        else:
            await pubsub.unsubscribe()
        await pubsub.close()

    async def listen(self, pubsub: PubSub):
        """Асинхронный генератор для прослушивания сообщений"""
        async for message in pubsub.listen():
            if message["type"] == "message":
                yield message["data"]


redis_client = RedisClient()
redis_pubsub = RedisPubSub(redis_client)
