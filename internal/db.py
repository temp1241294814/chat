from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from models import Base
import os

# DB_URL = "mysql+aiomysql://root@db:3306/chatapp?charset=utf8"
DB_URL = os.environ.get("DB_URL", "sqlite+aiosqlite:///./local.db")

async_engine = create_async_engine(DB_URL, echo=True)
async_session_maker = async_sessionmaker(async_engine, expire_on_commit=False)


async def create_db_and_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
