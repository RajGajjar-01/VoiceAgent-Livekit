from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# Managed Postgres / proxies silently drop idle connections; pre_ping catches
# a dead one before use, and recycle retires them before the idle cutoff.
engine = create_async_engine(
    settings.database_url, pool_size=5, max_overflow=10, pool_pre_ping=True, pool_recycle=300
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
