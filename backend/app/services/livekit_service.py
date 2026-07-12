import json

from livekit import api

from app.core.config import settings


def mint_token(user_id: str, display_name: str | None) -> tuple[str, str]:
    """Mints a LiveKit room-join token for the given user."""

    room_name = f"assistant-{user_id}"
    token = (
        api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
        .with_identity(user_id)
        .with_name(display_name or user_id)
        .with_metadata(json.dumps({"user_id": user_id}))
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
    )
    return token.to_jwt(), room_name
