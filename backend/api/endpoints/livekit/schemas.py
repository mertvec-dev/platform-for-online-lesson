"""Схемы для аудита токенов LiveKit"""

from datetime import datetime

from pydantic import BaseModel, Field


class LivekitTokenRead(BaseModel):
    id: int
    course_id: int
    user_id: int
    participant_identity: str
    token_jti: str | None
    session_id: str | None
    joined_at: datetime
    left_at: datetime | None
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime


class LivekitTokenListItem(BaseModel):
    id: int
    course_id: int
    user_id: int
    participant_identity: str
    session_id: str | None
    expires_at: datetime | None


class UpdateLivekitTokenAudit(BaseModel):
    left_at: datetime | None = Field(default=None)
