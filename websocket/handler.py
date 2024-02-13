import asyncio
import json
import uuid
from fastapi import APIRouter, WebSocket
from requests import session
from aggregation import NotificationAggregation

from dependencies import RDBSession, RedisClient
from internal.message_store import MessageStore
from internal.notification import publish
from models import Room, User
from schema import ClientEvent, InitialData, ServerEvent
from redis.asyncio.client import PubSub

router = APIRouter(tags=["websocket"])


def channel(room_id: int):
    return f"room:{room_id}"


async def ws_from_client(
    message_store: MessageStore,
    redis_client: RedisClient,
    websocket: WebSocket,
    db: RDBSession,
    room_id: int,
    user_id: int,
    session_id: str,
):
    # Client -> Server
    async for event_text in websocket.iter_text():
        client_event = ClientEvent.model_validate_json(event_text)
        server_event = None

        # イベントタイプによって処理を分ける
        match client_event.event_type:
            case "post":
                msg = await message_store.post_message(client_event.message)  # type: ignore
                server_event = ServerEvent(session_id=session_id, event_type="post", message=msg)
            case "delete":
                msg = await message_store.delete_message(client_event.message_id)  # type: ignore
                server_event = ServerEvent(
                    session_id=session_id,
                    event_type="delete", message_id=msg.message_id
                )
            case "mark":
                # 大小比較してもよいが、既読を巻き戻すこともありうるので、とりあえずはそのまま
                await redis_client.hset(f"marks:{room_id}", str(user_id), client_event.message_id)  # type: ignore
                server_event = ServerEvent(
                    session_id=session_id,
                    event_type="mark", message_id=client_event.message_id, user_id=user_id
                )

        if server_event:
            # 他のサーバーに通知する
            await redis_client.publish(
                channel(room_id), server_event.model_dump_json(exclude_unset=True)
            )

        # 通知を送る
        if client_event.event_type == "post":
            await _notify(db, user_id, room_id, client_event, redis_client)


async def _notify(db, user_id, room_id, client_event, redis_client):
    """通知を送る"""
    # DBからユーザーとルームを取得
    room = await Room.get_room_by_id(db, room_id, user_id)
    user = await User.get_by_id(db, user_id)
    if not room or not user:
        return
    notifications = await NotificationAggregation.notification_in_room(db, room_id)
    active_users = [int(u) for u in await redis_client.smembers(f"members:{room_id}")]  # type: ignore

    email_notification = {
        "to_emails": [],
        "subject": f"New message in {room.room_name}",
        "body": f"{user.username}: {client_event.message}",
    }
    push_notification = {
        "user_name": user_id,
        "room_id": room_id,
        "message": f"{user.username}: {client_event.message}",
        "tokens": []
    }
    for notification in notifications:
        if notification.user_id in active_users:
            # 現在オンラインのユーザーには通知しない
            continue
        match notification.notification_type:
            case "email":
                if notification.email:
                    email_notification["to_emails"].append(notification.email)
            case "push":
                if notification.tokens:
                    push_notification["tokens"] += notification.tokens
        if email_notification["to_emails"]:
            publish("email", email_notification)
        if push_notification.get("tokens"):
            publish("push", push_notification)


async def ws_from_another(
    pubsub: PubSub,
    websocket: WebSocket,
    session_id: str,
):
    # Server -> Client
    while True:
        message = await pubsub.get_message(ignore_subscribe_messages=True)
        if message:
            data = json.loads(message["data"].decode("utf-8"))
            if session_id == data["session_id"] and data["event_type"] == "mark":
                # 自分が送信した既読は無視する
                continue
            del data["session_id"]
    
            await websocket.send_json(data)


@router.websocket("/rooms/{room_id}/ws")
async def websocket_endpoint(
    room_id: int, websocket: WebSocket, db: RDBSession, redis_client: RedisClient
):
    # サーバーを識別するためのセッションIDを生成
    session_id = uuid.uuid4().hex
    
    await websocket.accept()

    # token JSONを受け取る
    try:
        token = await websocket.receive_json()
    except ValueError:
        await websocket.close()
        return

    # tokenを検証する
    user_id = await redis_client.get(token["token"])  # type: ignore
    if not user_id:
        await websocket.close()
        return
    user_id = int(user_id)

    # ルームにユーザーを追加
    await redis_client.sadd(f"members:{room_id}", user_id)  # type: ignore
    print(f"add user {user_id} to room {room_id}")

    store = MessageStore(room_id, user_id)
    async with redis_client.pubsub() as pubsub:
        await pubsub.subscribe(channel(room_id))
        task1 = asyncio.create_task(ws_from_another(pubsub, websocket, session_id))
        task2 = asyncio.create_task(
            ws_from_client(store, redis_client, websocket, db, room_id, user_id, session_id)
        )

        # 初期データを送信
        messages = await store.get_history(10)
        last_message_id = messages[-1].message_id if messages else 0
        result = await redis_client.hgetall(f"marks:{room_id}")  # type: ignore
        marks = {int(k): v for k, v in result.items()}
        await websocket.send_text(
            ServerEvent(
                session_id=session_id,
                event_type="init",
                initial_data=InitialData(messages=messages, marks=marks),
            ).model_dump_json(exclude_unset=True)
        )
        await redis_client.hset(f"marks:{room_id}", str(user_id), last_message_id)  # type: ignore

        # 終了を待つ
        _, pending = await asyncio.wait(
            [task1, task2], return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()

    # ルームからユーザーを削除
    await redis_client.srem(f"members:{room_id}", user_id)  # type: ignore
    print(f"remove user {user_id} from room {room_id}")
