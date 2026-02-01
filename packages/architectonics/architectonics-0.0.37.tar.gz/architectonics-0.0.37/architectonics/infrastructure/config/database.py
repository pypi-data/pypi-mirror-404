from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from architectonics.infrastructure.config.database_settings import database_settings


def get_engine() -> AsyncEngine:
    return create_async_engine(
        database_settings.DATABASE_CONNECTION_STRING,
        future=True,
        echo=False,
    )


def get_session(engine: AsyncEngine) -> sessionmaker:
    return sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
