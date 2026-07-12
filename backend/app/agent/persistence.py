import asyncio
from collections.abc import Coroutine

from livekit.agents import AgentSession, ChatMessage, ConversationItemAddedEvent

from app.core.database import SessionLocal
from app.repositories.conversation_repository import ConversationRepository

_background_tasks: set[asyncio.Task[None]] = set()


def _fire_and_forget(coro: Coroutine[None, None, None]) -> None:
    """AgentSession emits events synchronously (EventEmitter.emit calls
    callbacks directly, it does not await coroutines), so persisting a
    message can't just be `await`ed inside the event handler. asyncio only
    holds a weak reference to a bare create_task() result, so the task is
    kept alive here until it completes rather than risking it being
    garbage-collected mid-write."""
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


async def start_conversation(user_id: str, room: str) -> str:
    async with SessionLocal() as db_session:
        conversation = await ConversationRepository(db_session).start(user_id=user_id, room=room)
        return str(conversation.id)


async def end_conversation(conversation_id: str) -> None:
    async with SessionLocal() as db_session:
        await ConversationRepository(db_session).end(conversation_id)


async def _save_message(conversation_id: str, role: str, content: str) -> None:
    async with SessionLocal() as db_session:
        await ConversationRepository(db_session).add_message(
            conversation_id=conversation_id, role=role, content=content
        )


def register_persistence(session: AgentSession[None], conversation_id: str) -> None:
    def on_item_added(event: ConversationItemAddedEvent) -> None:
        if not isinstance(event.item, ChatMessage) or event.item.role not in ("user", "assistant"):
            return
        text = event.item.text_content
        if not text:
            return
        _fire_and_forget(_save_message(conversation_id, event.item.role, text))

    session.on("conversation_item_added", on_item_added)
