import asyncio
import json
import logging
from datetime import datetime
from typing import Any

from livekit.agents import Agent, AgentSession, APIStatusError, ErrorEvent, JobContext, WorkerOptions, cli
from livekit.agents.llm import LLM, AvailabilityChangedEvent, FallbackAdapter, LLMError
from livekit.plugins import deepgram, elevenlabs, openai, silero

from app.agent.persistence import (
    end_conversation,
    register_persistence,
    start_conversation,
)
from app.agent.prompts import build_system_prompt
from app.agent.tools import build_tools
from app.core.config import settings

logger = logging.getLogger("app.agent.worker")

RATE_LIMIT_MESSAGE = "The AI assistant hit its usage rate limit. Please wait a moment and try again."
LLM_UNAVAILABLE_MESSAGE = "The AI assistant is temporarily unavailable. Please try again shortly."


def _is_rate_limit_error(error: BaseException) -> bool:
    return isinstance(error, APIStatusError) and error.status_code == 429


class _LLMHealth:
    """Tracks whether the most recent LLM failure was a 429.

    FallbackAdapter re-raises a generic APIConnectionError once every
    instance in the chain has failed, losing the original status code —
    so the per-instance listeners below record it here before that happens.
    """

    def __init__(self) -> None:
        self.last_error_was_rate_limit = False


def _watch_llm_errors(llm_instance: LLM[Any], label: str, health: _LLMHealth) -> None:
    def _on_error(error: LLMError) -> None:
        if _is_rate_limit_error(error.error):
            health.last_error_was_rate_limit = True
            logger.warning("%s hit a rate limit (429), recoverable=%s", label, error.recoverable)
        else:
            health.last_error_was_rate_limit = False
            if not error.recoverable:
                logger.error("%s failed: %s", label, error.error)

    llm_instance.on("error", _on_error)


def _build_llm(health: _LLMHealth) -> LLM[Any]:
    primary = openai.LLM(model=settings.LLM_MODEL, api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)
    _watch_llm_errors(primary, "primary LLM (Groq)", health)

    if not settings.CLOUDFLARE_ACCOUNT_ID or not settings.CLOUDFLARE_API_KEY:
        return primary

    # Cloudflare Workers AI exposes an OpenAI-compatible endpoint, so it's a
    # drop-in second openai.LLM — falls back here when the primary provider
    # errors (e.g. Groq's free-tier rate limits).
    fallback = openai.LLM(
        model=settings.FALLBACK_LLM_MODEL,
        api_key=settings.CLOUDFLARE_API_KEY,
        base_url=f"https://api.cloudflare.com/client/v4/accounts/{settings.CLOUDFLARE_ACCOUNT_ID}/ai/v1",
    )
    _watch_llm_errors(fallback, "fallback LLM (Cloudflare)", health)

    adapter = FallbackAdapter([primary, fallback])

    def _on_availability_changed(event: AvailabilityChangedEvent) -> None:
        if event.available:
            logger.info("%s recovered, back in rotation", event.llm.label)
        else:
            logger.warning("%s unavailable, switching to fallback", event.llm.label)

    adapter.on("llm_availability_changed", _on_availability_changed)
    return adapter


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    # Room is named "assistant-{user_id}-{conversation-uuid}" by
    # livekit_service.mint_token — this is how the worker learns which user
    # it's serving, since it runs outside FastAPI's request/response cycle
    # and has no other channel to receive that context at job start. user_id
    # is a UUID (36 chars) and itself contains dashes, so it must be sliced
    # by fixed length rather than split on "-".
    user_id = ctx.room.name.removeprefix("assistant-")[:36]

    conversation_id = await start_conversation(user_id, ctx.room.name)
    ctx.add_shutdown_callback(lambda: end_conversation(conversation_id))

    tts = (
        elevenlabs.TTS(api_key=settings.ELEVENLABS_API_KEY, voice_id=settings.ELEVENLABS_VOICE_ID)
        if settings.ELEVENLABS_VOICE_ID
        else elevenlabs.TTS(api_key=settings.ELEVENLABS_API_KEY)
    )
    llm_health = _LLMHealth()
    session: AgentSession[None] = AgentSession(
        stt=deepgram.STT(api_key=settings.DEEPGRAM_API_KEY),
        llm=_build_llm(llm_health),
        tts=tts,
        vad=silero.VAD.load(),
    )
    register_persistence(session, conversation_id)

    def _on_session_error(error_event: ErrorEvent) -> None:
        # Every LLM in the fallback chain has now failed for this turn —
        # session-level "error" only fires once FallbackAdapter itself gives
        # up, so this is the point to surface something to the user instead
        # of leaving the call silently stuck.
        if error_event.error.type != "llm_error" or error_event.error.recoverable:
            return

        message = RATE_LIMIT_MESSAGE if llm_health.last_error_was_rate_limit else LLM_UNAVAILABLE_MESSAGE
        asyncio.create_task(_notify_frontend(ctx, message))

    session.on("error", _on_session_error)

    agent = Agent(instructions=build_system_prompt(datetime.now().astimezone()), tools=build_tools(user_id))
    await session.start(agent=agent, room=ctx.room)


async def _notify_frontend(ctx: JobContext, message: str) -> None:
    payload = json.dumps({"type": "agent_error", "message": message}).encode("utf-8")
    try:
        await ctx.room.local_participant.publish_data(payload, reliable=True, topic="agent-error")
    except Exception:
        logger.exception("failed to publish agent error notification to frontend")


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            ws_url=settings.LIVEKIT_URL,
            api_key=settings.LIVEKIT_API_KEY,
            api_secret=settings.LIVEKIT_API_SECRET,
        )
    )
