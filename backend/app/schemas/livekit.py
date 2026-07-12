from pydantic import BaseModel


class LiveKitTokenResponse(BaseModel):
    token: str
    url: str
    room: str
