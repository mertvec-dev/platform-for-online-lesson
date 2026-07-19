"""Сервис LiveKit Egress — запуск/остановка записи занятий + presigned URL."""

import logging

from livekit import api
from livekit.api import RoomCompositeEgressRequest, StopEgressRequest

from backend.api.core.config import settings

logger = logging.getLogger(__name__)


class EgressService:
    """Управление записью занятий через LiveKit Egress API"""

    def __init__(self) -> None:
        self._lkapi: api.LiveKitAPI | None = None

    @property
    def lkapi(self) -> api.LiveKitAPI:
        if self._lkapi is None:
            self._lkapi = api.LiveKitAPI(
                url="http://livekit:7880",
                api_key=settings.LIVEKIT_API_KEY,
                api_secret=settings.LIVEKIT_API_SECRET,
            )
        return self._lkapi

    async def start_recording(self, room_name: str) -> str | None:
        """Запускает композитную запись комнаты. Возвращает egress_id"""
        if not settings.LIVEKIT_EGRESS_ENABLED:
            logger.debug("Egress отключён (LIVEKIT_EGRESS_ENABLED=false)")
            return None

        try:
            request = RoomCompositeEgressRequest(
                room_name=room_name,
                file_outputs=[
                    {
                        "file_type": "mp4",
                        "s3": {
                            "access_key": settings.S3_ACCESS_KEY,
                            "secret": settings.S3_SECRET_KEY,
                            "bucket": settings.S3_BUCKET,
                            "region": settings.S3_REGION,
                            "endpoint": settings.S3_ENDPOINT,
                        },
                    }
                ],
            )
            response = await self.lkapi.egress.start_room_composite_egress(request)
            egress_id = response.egress_id
            logger.info("Egress запущен: egress_id=%s, room=%s", egress_id, room_name)
            return egress_id
        except Exception:
            logger.exception("Ошибка запуска Egress для комнаты %s", room_name)
            return None

    async def stop_recording(self, egress_id: str) -> None:
        """Останавливает запись по egress_id."""
        try:
            request = StopEgressRequest(egress_id=egress_id)
            await self.lkapi.egress.stop_egress(request)
            logger.info("Egress остановлен: egress_id=%s", egress_id)
        except Exception:
            logger.exception("Ошибка остановки Egress: egress_id=%s", egress_id)


async def generate_presigned_url(s3_path: str) -> str:
    """
    Генерирует временную presigned URL для доступа к файлу в S3/MinIO.

    В dev-окружении MinIO файлы публично доступны — возвращаем прямую ссылку.
    Для production нужно подключить boto3 для настоящей presigned URL.

    s3_path — полный путь вида s3://bucket/key.mp4 или просто key.mp4.
    """
    endpoint = settings.S3_ENDPOINT.rstrip("/")
    bucket = settings.S3_BUCKET

    if s3_path.startswith("s3://"):
        key = s3_path.split("/", 3)[-1]
    else:
        key = s3_path.lstrip("/")

    return f"{endpoint}/{bucket}/{key}"


egress_service = EgressService()
