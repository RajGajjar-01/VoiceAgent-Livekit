from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli
from livekit.plugins import deepgram, elevenlabs, openai, silero

from app.agent.prompts import SYSTEM_PROMPT
from app.core.config import settings


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    # Room is named "assistant-{user_id}" by livekit_service.mint_token —
    # this is how the worker learns which user it's serving, since it runs
    # outside FastAPI's request/response cycle and has no other channel to
    # receive that context at job start.
    user_id = ctx.room.name.removeprefix("assistant-")  # noqa: F841 — wired into tools in a later step

    tts = (
        elevenlabs.TTS(api_key=settings.ELEVENLABS_API_KEY, voice_id=settings.ELEVENLABS_VOICE_ID)
        if settings.ELEVENLABS_VOICE_ID
        else elevenlabs.TTS(api_key=settings.ELEVENLABS_API_KEY)
    )
    session: AgentSession[None] = AgentSession(
        stt=deepgram.STT(api_key=settings.DEEPGRAM_API_KEY),
        llm=openai.LLM(model=settings.LLM_MODEL, api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL),
        tts=tts,
        vad=silero.VAD.load(),
    )
    agent = Agent(instructions=SYSTEM_PROMPT)
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
