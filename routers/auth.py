from fastapi import APIRouter, HTTPException, Response
from models import (
    User,
)
from internal.auth import encrypt_password, generate_token
from schema import (
    CreateUserResponse,
    CreateUserRequest,
    LoginRequest,
)
from dependencies import RDBSession, RedisClient

router = APIRouter(tags=["auth"])


@router.post("/register")
async def register(body: CreateUserRequest, db: RDBSession):
    """ユーザー登録"""
    user = await User.add(
        db,
        body.username,
        body.email,
        encrypt_password(body.password),
    )
    return CreateUserResponse(
        user_id=user.user_id, username=user.username, email=user.email
    )


@router.post("/login")
async def login(
    db: RDBSession, redis_client: RedisClient, response: Response, body: LoginRequest
):
    """ログイン"""
    user = await User.authenticate_user(db, body.username, body.password)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    access_token = generate_token()
    # トークンを保存しておく(1週間)
    await redis_client.set(access_token, user.user_id, ex=60 * 60 * 24 * 7)

    response.set_cookie(
        "sessionid", access_token, httponly=True, max_age=60 * 60 * 24 * 7
    )
    return {"message": "Login successful"}
