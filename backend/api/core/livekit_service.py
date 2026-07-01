"""Сервис LiveKit: генерация токенов, имена комнат."""

from datetime import timedelta

from livekit import api

from backend.api.core.config import settings

TOKEN_TTL_SECONDS = 3600  # 1 час


class LiveKitService:
    """Генерация LiveKit-токенов для подключения к комнате."""

    def generate_token(
        self,
        room_name: str,
        participant_id: str,
        participant_name: str,
    ) -> str:
        """Access Token для участника: VideoGrants с join + publish + subscribe."""
        token = (
            api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
            .with_identity(participant_id)
            .with_name(participant_name)
            .with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=room_name,
                    can_publish=True,
                    can_subscribe=True,
                )
            )
            .with_ttl(timedelta(seconds=TOKEN_TTL_SECONDS))
        )
        return token.to_jwt()

    def room_name(self, course_id: int, lesson_id: int) -> str:
        return f"course_{course_id}_lesson_{lesson_id}"
