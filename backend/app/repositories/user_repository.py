from datetime import datetime

from sqlalchemy import select

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    async def get_by_id(self, user_id: str) -> User | None:
        return await self._session.get(User, user_id)

    async def get_by_google_id(self, google_id: str) -> User | None:
        result = await self._session.execute(select(User).where(User.google_id == google_id))
        return result.scalar_one_or_none()

    async def upsert_from_google(
        self,
        google_id: str,
        email: str,
        name: str | None,
        avatar_url: str | None,
        encrypted_refresh_token: str | None,
        encrypted_access_token: str | None = None,
        access_token_expiry: datetime | None = None,
    ) -> User:
        user = await self.get_by_google_id(google_id)
        if user is None:
            user = User(google_id=google_id, email=email)
            self._session.add(user)

        user.email = email
        user.name = name
        user.avatar_url = avatar_url
        if encrypted_refresh_token is not None:
            user.google_refresh_token = encrypted_refresh_token
        if encrypted_access_token is not None:
            user.google_access_token = encrypted_access_token
            user.google_token_expiry = access_token_expiry

        await self._session.commit()
        await self._session.refresh(user)
        return user
