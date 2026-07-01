"""Сервис чат-сообщений: сохранение, история, пагинация"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....models import ChatMessage

logger = logging.getLogger(__name__)


class ChatMessageService:
    PAGE_SIZE = 50

    async def save(
        self,
        course_id: int,
        author_id: int,
        text: str,
        db: AsyncSession,
    ) -> ChatMessage:
        msg = ChatMessage(
            course_id=course_id,
            author_id=author_id,
            text=text,
        )
        db.add(msg)
        await db.commit()
        logger.info(
            "Сохранено сообщение в чате курса: message_id=%d, course_id=%d, author_id=%d",
            msg.id,
            course_id,
            author_id,
        )
        return msg

    async def get_history(
        self,
        course_id: int,
        db: AsyncSession,
        *,
        before_id: int | None = None,
    ) -> list[ChatMessage]:
        statement = (
            select(ChatMessage)
            .where(ChatMessage.course_id == course_id)  # type: ignore[arg-type]
            .order_by(ChatMessage.created_at.desc())  # type: ignore[attr-define]
            .limit(self.PAGE_SIZE)
        )
        if before_id is not None:
            sub_stmt = select(ChatMessage.created_at).where(  # type: ignore[arg-type]
                ChatMessage.id == before_id
            )
            statement = statement.where(
                ChatMessage.created_at < sub_stmt.scalar_subquery()
            )

        result = await db.execute(statement)

        return list(reversed(result.scalars().all()))


chat_message_service = ChatMessageService()
