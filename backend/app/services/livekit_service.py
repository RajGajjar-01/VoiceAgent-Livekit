import json
import uuid

from livekit import api

from app.core.config import settings


def mint_token(user_id: str, display_name: str | None) -> tuple[str, str]:
    """Mints a LiveKit room-join token for the given user.

    Each call gets a unique room name rather than a static "assistant-{user_id}"
    — LiveKit only auto-dispatches an agent job when a room is newly created, not
    when a participant joins one that still exists. The previous agent's job
    process can take ~60s to fully tear down after its human participant leaves,
    during which the room is still technically alive; reusing the same room name
    let a quick "New conversation" retry silently rejoin that stale room with no
    agent ever getting (re)dispatched to it.
    """

    room_name = f"assistant-{user_id}-{uuid.uuid4()}"
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
