"""Standalone credential sanity check — makes one real, lightweight API call
per provider to confirm the keys in .env actually work, without spending
meaningful quota (no STT/LLM/TTS generation, just account/listing endpoints).

Run: cd backend && uv run python scripts/verify_creds.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402
from livekit import api  # noqa: E402

from app.core.config import settings  # noqa: E402


async def check_livekit() -> tuple[bool, str]:
    lkapi = api.LiveKitAPI(settings.LIVEKIT_URL, settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
    try:
        rooms = await lkapi.room.list_rooms(api.ListRoomsRequest())
        return True, f"connected, {len(rooms.rooms)} active room(s)"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
    finally:
        await lkapi.aclose()


async def check_deepgram() -> tuple[bool, str]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.deepgram.com/v1/projects",
            headers={"Authorization": f"Token {settings.DEEPGRAM_API_KEY}"},
        )
    if resp.status_code == 200:
        projects = resp.json().get("projects", [])
        return True, f"{len(projects)} project(s)"
    return False, f"HTTP {resp.status_code}: {resp.text[:200]}"


async def check_groq() -> tuple[bool, str]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.LLM_BASE_URL}/models",
            headers={"Authorization": f"Bearer {settings.LLM_API_KEY}"},
        )
    if resp.status_code != 200:
        return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
    model_ids = [m["id"] for m in resp.json().get("data", [])]
    note = "" if settings.LLM_MODEL in model_ids else f" (WARNING: LLM_MODEL={settings.LLM_MODEL!r} not found)"
    return True, f"{len(model_ids)} model(s) available{note}"


async def check_elevenlabs() -> tuple[bool, str]:
    # /v1/user requires the user_read permission scope, which restricted
    # keys often don't have — /v1/voices only needs voices_read, which is
    # what we actually rely on (picking a voice_id for TTS), so check that
    # instead of assuming a full-access key.
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.elevenlabs.io/v1/voices",
            headers={"xi-api-key": settings.ELEVENLABS_API_KEY},
        )
        if resp.status_code != 200:
            return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
        voice_count = len(resp.json().get("voices", []))

        voice_note = " (no ELEVENLABS_VOICE_ID set)"
        if settings.ELEVENLABS_VOICE_ID:
            voice_resp = await client.get(
                f"https://api.elevenlabs.io/v1/voices/{settings.ELEVENLABS_VOICE_ID}",
                headers={"xi-api-key": settings.ELEVENLABS_API_KEY},
            )
            voice_note = " | voice_id OK" if voice_resp.status_code == 200 else f" | voice_id HTTP {voice_resp.status_code}"

    return True, f"{voice_count} voice(s) visible to this key{voice_note}"


async def main() -> None:
    checks: list[tuple[str, object]] = [
        ("LiveKit", check_livekit),
        ("Deepgram (STT)", check_deepgram),
        ("Groq (LLM)", check_groq),
        ("ElevenLabs (TTS)", check_elevenlabs),
    ]
    all_ok = True
    for name, fn in checks:
        try:
            ok, detail = await fn()  # type: ignore[operator]
        except Exception as exc:  # noqa: BLE001
            ok, detail = False, f"unexpected error: {exc}"
        all_ok = all_ok and ok
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
