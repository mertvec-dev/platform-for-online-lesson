"""Сервис LiveKit: генерация токенов, имена комнат."""

import logging
from datetime import timedelta

from livekit import api

from backend.api.core.config import settings

logger = logging.getLogger(__name__)


class LiveKitService:
    """Генерация LiveKit-токенов для подключения к комнате."""

    def generate_token(
        self,
        room_name: str,
        participant_id: str,
        participant_name: str,
        *,
        can_publish: bool = True,
    ) -> str:
        """Access Token для участника: VideoGrants с join + publish + subscribe.

        can_publish=False — режим тамбура (только просмотр, без камеры/микрофона).
        """
        token = (
            api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
            .with_identity(participant_id)
            .with_name(participant_name)
            .with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=room_name,
                    can_publish=can_publish,
                    can_subscribe=can_publish,
                )
            )
            .with_ttl(timedelta(seconds=settings.LIVEKIT_TOKEN_TTL_SECONDS))
        )
        jwt_token = token.to_jwt()
        logger.info(
            "LiveKit-токен выдан: room=%s, participant=%s, publish=%s",
            room_name, participant_id, can_publish,
        )
        return jwt_token

    def room_name(self, course_id: int, lesson_id: int) -> str:
        return f"course_{course_id}_lesson_{lesson_id}"
