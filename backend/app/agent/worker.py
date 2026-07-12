from datetime import datetime
from typing import Any

from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli
from livekit.agents.llm import LLM, FallbackAdapter
from livekit.plugins import deepgram, elevenlabs, openai, silero

from app.agent.persistence import (
    end_conversation,
    register_persistence,
    start_conversation,
)
from app.agent.prompts import build_system_prompt
from app.agent.tools import build_tools
from app.core.config import settings


def _build_llm() -> LLM[Any]:
    primary = openai.LLM(model=settings.LLM_MODEL, api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)
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
    return FallbackAdapter([primary, fallback])


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
    session: AgentSession[None] = AgentSession(
        stt=deepgram.STT(api_key=settings.DEEPGRAM_API_KEY),
        llm=_build_llm(),
        tts=tts,
        vad=silero.VAD.load(),
    )
    register_persistence(session, conversation_id)
    agent = Agent(instructions=build_system_prompt(datetime.now().astimezone()), tools=build_tools(user_id))
    await session.start(agent=agent, room=ctx.room)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            ws_url=settings.LIVEKIT_URL,
            api_key=settings.LIVEKIT_API_KEY,
            api_secret=settings.LIVEKIT_API_SECRET,
        )
    )
