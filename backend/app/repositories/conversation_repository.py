from datetime import UTC, datetime

from sqlalchemy import select

from app.models.conversation import Conversation
from app.models.conversation_message import ConversationMessage
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository):
    async def start(self, user_id: str, room: str) -> Conversation:
        conversation = Conversation(user_id=user_id, room=room)
        self._session.add(conversation)
        await self._session.commit()
        await self._session.refresh(conversation)
        return conversation

    async def end(self, conversation_id: str) -> None:
        conversation = await self._session.get(Conversation, conversation_id)
        if conversation is None:
            return
        conversation.ended_at = datetime.now(UTC)
        await self._session.commit()

    async def add_message(self, conversation_id: str, role: str, content: str) -> ConversationMessage:
        message = ConversationMessage(conversation_id=conversation_id, role=role, content=content)
        self._session.add(message)
        await self._session.commit()
        await self._session.refresh(message)
        return message

    async def list_for_user(self, user_id: str) -> list[Conversation]:
        result = await self._session.execute(
            select(Conversation).where(Conversation.user_id == user_id).order_by(Conversation.started_at.desc())
        )
        return list(result.scalars().all())

    async def get_messages(self, conversation_id: str, user_id: str) -> list[ConversationMessage] | None:
        conversation = await self._session.get(Conversation, conversation_id)
        if conversation is None or str(conversation.user_id) != user_id:
            return None
        result = await self._session.execute(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at.asc())
        )
        return list(result.scalars().all())
