# FastAPIのdependencyを定義するファイル

from typing import Annotated
from fastapi import Cookie, Depends, HTTPException
from internal.db import AsyncSession, get_async_session
import redis.asyncio as redis
import os

redis_cli = redis.from_url(os.environ.get("REDIS_HOST", "redis://localhost"))
RDBSession = Annotated[AsyncSession, Depends(get_async_session)]


def get_redis_client() -> redis.Redis:
    return redis_cli


RedisClient = Annotated[redis.Redis, Depends(get_redis_client)]


async def get_current_user_id(r: RedisClient, sessionid: str = Cookie(None)):
    """セッションから、ユーザIDを取得する"""
    try:
        user_id = await r.get(sessionid)
    except redis.DataError:
        user_id = None
    if user_id is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return int(user_id)


CurrentUser = Annotated[int, Depends(get_current_user_id)]
