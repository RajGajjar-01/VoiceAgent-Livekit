from pydantic import BaseModel


class UserProfileResponse(BaseModel):
    id: str
    email: str
    name: str | None
    avatar_url: str | None
