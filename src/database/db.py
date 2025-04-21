import contextlib
import asyncpg
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.engine import URL
from src.conf.config import config


class DatabaseSessionManager:
    def __init__(self, url: str):
        self.url = url
        self._engine: AsyncEngine | None = None
        self._session_maker: async_sessionmaker | None = None

    async def init(self):
        await self._ensure_database_exists()
        self._engine = create_async_engine(self.url)
        self._session_maker = async_sessionmaker(
            autoflush=False, autocommit=False, bind=self._engine
        )

    async def _ensure_database_exists(self):
        db_name = config.POSTGRES_DB
        conn_url = f"postgresql://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@{config.POSTGRES_HOST}:{config.POSTGRES_PORT}/postgres"
        conn = await asyncpg.connect(conn_url)
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname=$1", db_name
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{db_name}"')
        await conn.close()

    @contextlib.asynccontextmanager
    async def session(self):
        if self._session_maker is None:
            raise Exception("Database session is not initialized")
        session = self._session_maker()
        try:
            yield session
        except SQLAlchemyError:
            await session.rollback()
            raise
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(config.DATABASE_URL)


async def get_db():
    async with sessionmanager.session() as session:
        yield session
