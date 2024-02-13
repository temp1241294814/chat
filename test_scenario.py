import asyncio
from email import message
import json
import websockets
from datetime import datetime
import httpx
import random

def random_string(n=10):
    return "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=n))

async def ws(room_id, user, solo=False):

    async with httpx.AsyncClient() as client:
        await client.post("http://localhost:8000/login", json={
            "username": user["username"],
            "password": "password",
        })
        token = client.cookies["sessionid"]

    async with websockets.connect(f"ws://localhost:8000/rooms/{room_id}/ws") as websocket:
        # 最初にトークンを送信
        await websocket.send(json.dumps({"token": token}))

        # サーバーからの初期データを受信
        init = json.loads(await websocket.recv())
        print(f"{user['username']}: Connected to the server with initial data: {init}")

        if solo:
            return

        for i in range(5):
            # メッセージを送信
            await websocket.send(json.dumps({"event_type": "post", "message": f"Hello, World ({i+1}/5) from {user['username']}!"}))
            await asyncio.sleep(0.5)

        for i in range(20):
            response = json.loads(await websocket.recv())
            print(f"{user['username']}: Received from server: {response}")
            if response.get("event_type") == "post":
                # メッセージを受信したら既読にする
                await websocket.send(
                    json.dumps({"event_type": "mark", "message_id": response.get("message", {}).get("message_id")})
                )


async def test_scenario():
    # ユーザーを3人作成
    users = []
    room = None
    async with httpx.AsyncClient() as client:
        for _ in range(5):
            res = await client.post("http://localhost:8000/register", json={
                "username": random_string(),
                "password": "password",
                "email": f"{random_string()}@example.com",
            })
            users.append(res.json())

        # ログイン
        await client.post("http://localhost:8000/login", json={
            "username": users[0]["username"],
            "password": "password",
        })

        res = await client.post("http://localhost:8000/rooms", json={
            "room_type": "group",
            "room_name": "test_room_" + random_string(),
            "initial_members": [user["user_id"] for user in users],
        })
        room = res.json()

        # Eメール通知を設定
        await client.post("http://localhost:8000/settings/notification", json={
            "notification_type": "email",
        })
    
    t1 = asyncio.create_task(ws(room["room_id"], users[1]))
    t2 = asyncio.create_task(ws(room["room_id"], users[2]))

    await asyncio.wait([t1, t2])

    await ws(room["room_id"], users[2], solo=True)


asyncio.run(test_scenario())

"""
出力例
wgtvvxbrup: Connected to the server with initial data: {'session_id': 'aa07ad520e254adea93e3d9126d6c6e7', 'event_type': 'init', 'initial_data': {'messages': [], 'marks': {}}}
qniohmhkir: Connected to the server with initial data: {'session_id': '054b8957b8804a829afba559422566ee', 'event_type': 'init', 'initial_data': {'messages': [], 'marks': {}}}
wgtvvxbrup: Received from server: {'event_type': 'post', 'message': {'message_id': '1707846114970:324', 'room_id': 47, 'user_id': 324, 'message': 'Hello, World (1/5) from wgtvvxbrup!', 'deleted': False, 'created_at': 1707846114970}}
wgtvvxbrup: Received from server: {'event_type': 'post', 'message': {'message_id': '1707846114971:325', 'room_id': 47, 'user_id': 325, 'message': 'Hello, World (1/5) from qniohmhkir!', 'deleted': False, 'created_at': 1707846114971}}
wgtvvxbrup: Received from server: {'event_type': 'post', 'message': {'message_id': '1707846115472:324', 'room_id': 47, 'user_id': 324, 'message': 'Hello, World (2/5) from wgtvvxbrup!', 'deleted': False, 'created_at': 1707846115472}}
wgtvvxbrup: Received from server: {'event_type': 'post', 'message': {'message_id': '1707846115472:325', 'room_id': 47, 'user_id': 325, 'message': 'Hello, World (2/5) from qniohmhkir!', 'deleted': False, 'created_at': 1707846115472}}
wgtvvxbrup: Received from server: {'event_type': 'post', 'message': {'message_id': '1707846115973:324', 'room_id': 47, 'user_id': 324, 'message': 'Hello, World (3/5) from wgtvvxbrup!', 'deleted': False, 'created_at': 1707846115973}}
wgtvvxbrup: Received from server: {'event_type': 'post', 'message': {'message_id': '1707846115973:325', 'room_id': 47, 'user_id': 325, 'message': 'Hello, World (3/5) from qniohmhkir!', 'deleted': False, 'created_at': 1707846115973}}
wgtvvxbrup: Received from server: {'event_type': 'post', 'message': {'message_id': '1707846116474:324', 'room_id': 47, 'user_id': 324, 'message': 'Hello, World (4/5) from wgtvvxbrup!', 'deleted': False, 'created_at': 1707846116474}}
wgtvvxbrup: Received from server: {'event_type': 'post', 'message': {'message_id': '1707846116474:325', 'room_id': 47, 'user_id': 325, 'message': 'Hello, World (4/5) from qniohmhkir!', 'deleted': False, 'created_at': 1707846116474}}
wgtvvxbrup: Received from server: {'event_type': 'post', 'message': {'message_id': '1707846116975:324', 'room_id': 47, 'user_id': 324, 'message': 'Hello, World (5/5) from wgtvvxbrup!', 'deleted': False, 'created_at': 1707846116975}}
wgtvvxbrup: Received from server: {'event_type': 'post', 'message': {'message_id': '1707846116976:325', 'room_id': 47, 'user_id': 325, 'message': 'Hello, World (5/5) from qniohmhkir!', 'deleted': False, 'created_at': 1707846116976}}
qniohmhkir: Received from server: {'event_type': 'post', 'message': {'message_id': '1707846114970:324', 'room_id': 47, 'user_id': 324, 'message': 'Hello, World (1/5) from wgtvvxbrup!', 'deleted': False, 'created_at': 1707846114970}}
qniohmhkir: Received from server: {'event_type': 'post', 'message': {'message_id': '1707846114971:325', 'room_id': 47, 'user_id': 325, 'message': 'Hello, World (1/5) from qniohmhkir!', 'deleted': False, 'created_at': 1707846114971}}
qniohmhkir: Received from server: {'event_type': 'post', 'message': {'message_id': '1707846115472:324', 'room_id': 47, 'user_id': 324, 'message': 'Hello, World (2/5) from wgtvvxbrup!', 'deleted': False, 'created_at': 1707846115472}}
qniohmhkir: Received from server: {'event_type': 'post', 'message': {'message_id': '1707846115472:325', 'room_id': 47, 'user_id': 325, 'message': 'Hello, World (2/5) from qniohmhkir!', 'deleted': False, 'created_at': 1707846115472}}
qniohmhkir: Received from server: {'event_type': 'post', 'message': {'message_id': '1707846115973:324', 'room_id': 47, 'user_id': 324, 'message': 'Hello, World (3/5) from wgtvvxbrup!', 'deleted': False, 'created_at': 1707846115973}}
qniohmhkir: Received from server: {'event_type': 'post', 'message': {'message_id': '1707846115973:325', 'room_id': 47, 'user_id': 325, 'message': 'Hello, World (3/5) from qniohmhkir!', 'deleted': False, 'created_at': 1707846115973}}
qniohmhkir: Received from server: {'event_type': 'post', 'message': {'message_id': '1707846116474:324', 'room_id': 47, 'user_id': 324, 'message': 'Hello, World (4/5) from wgtvvxbrup!', 'deleted': False, 'created_at': 1707846116474}}
qniohmhkir: Received from server: {'event_type': 'post', 'message': {'message_id': '1707846116474:325', 'room_id': 47, 'user_id': 325, 'message': 'Hello, World (4/5) from qniohmhkir!', 'deleted': False, 'created_at': 1707846116474}}
qniohmhkir: Received from server: {'event_type': 'post', 'message': {'message_id': '1707846116975:324', 'room_id': 47, 'user_id': 324, 'message': 'Hello, World (5/5) from wgtvvxbrup!', 'deleted': False, 'created_at': 1707846116975}}
qniohmhkir: Received from server: {'event_type': 'post', 'message': {'message_id': '1707846116976:325', 'room_id': 47, 'user_id': 325, 'message': 'Hello, World (5/5) from qniohmhkir!', 'deleted': False, 'created_at': 1707846116976}}
qniohmhkir: Received from server: {'event_type': 'mark', 'message_id': '1707846114970:324', 'user_id': 324}
wgtvvxbrup: Received from server: {'event_type': 'mark', 'message_id': '1707846114970:324', 'user_id': 325}
wgtvvxbrup: Received from server: {'event_type': 'mark', 'message_id': '1707846114971:325', 'user_id': 325}
qniohmhkir: Received from server: {'event_type': 'mark', 'message_id': '1707846114971:325', 'user_id': 324}
wgtvvxbrup: Received from server: {'event_type': 'mark', 'message_id': '1707846115472:324', 'user_id': 325}
qniohmhkir: Received from server: {'event_type': 'mark', 'message_id': '1707846115472:324', 'user_id': 324}
qniohmhkir: Received from server: {'event_type': 'mark', 'message_id': '1707846115472:325', 'user_id': 324}
wgtvvxbrup: Received from server: {'event_type': 'mark', 'message_id': '1707846115472:325', 'user_id': 325}
wgtvvxbrup: Received from server: {'event_type': 'mark', 'message_id': '1707846115973:324', 'user_id': 325}
qniohmhkir: Received from server: {'event_type': 'mark', 'message_id': '1707846115973:324', 'user_id': 324}
wgtvvxbrup: Received from server: {'event_type': 'mark', 'message_id': '1707846115973:325', 'user_id': 325}
qniohmhkir: Received from server: {'event_type': 'mark', 'message_id': '1707846115973:325', 'user_id': 324}
wgtvvxbrup: Received from server: {'event_type': 'mark', 'message_id': '1707846116474:324', 'user_id': 325}
qniohmhkir: Received from server: {'event_type': 'mark', 'message_id': '1707846116474:324', 'user_id': 324}
wgtvvxbrup: Received from server: {'event_type': 'mark', 'message_id': '1707846116474:325', 'user_id': 325}
qniohmhkir: Received from server: {'event_type': 'mark', 'message_id': '1707846116474:325', 'user_id': 324}
wgtvvxbrup: Received from server: {'event_type': 'mark', 'message_id': '1707846116975:324', 'user_id': 325}
qniohmhkir: Received from server: {'event_type': 'mark', 'message_id': '1707846116975:324', 'user_id': 324}
wgtvvxbrup: Received from server: {'event_type': 'mark', 'message_id': '1707846116976:325', 'user_id': 325}
qniohmhkir: Received from server: {'event_type': 'mark', 'message_id': '1707846116976:325', 'user_id': 324}
qniohmhkir: Connected to the server with initial data: {'session_id': '750020442f0547e598e45f067dc23750', 'event_type': 'init', 'initial_data': {'messages': [{'message_id': '1707846116976:325', 'room_id': 47, 'user_id': 325, 'message': 'Hello, World (5/5) from qniohmhkir!', 'deleted': False, 'created_at': 1707846116976}, {'message_id': '1707846116975:324', 'room_id': 47, 'user_id': 324, 'message': 'Hello, World (5/5) from wgtvvxbrup!', 'deleted': False, 'created_at': 1707846116975}, {'message_id': '1707846116474:325', 'room_id': 47, 'user_id': 325, 'message': 'Hello, World (4/5) from qniohmhkir!', 'deleted': False, 'created_at': 1707846116474}, {'message_id': '1707846116474:324', 'room_id': 47, 'user_id': 324, 'message': 'Hello, World (4/5) from wgtvvxbrup!', 'deleted': False, 'created_at': 1707846116474}, {'message_id': '1707846115973:325', 'room_id': 47, 'user_id': 325, 'message': 'Hello, World (3/5) from qniohmhkir!', 'deleted': False, 'created_at': 1707846115973}, {'message_id': '1707846115973:324', 'room_id': 47, 'user_id': 324, 'message': 'Hello, World (3/5) from wgtvvxbrup!', 'deleted': False, 'created_at': 1707846115973}, {'message_id': '1707846115472:325', 'room_id': 47, 'user_id': 325, 'message': 'Hello, World (2/5) from qniohmhkir!', 'deleted': False, 'created_at': 1707846115472}, {'message_id': '1707846115472:324', 'room_id': 47, 'user_id': 324, 'message': 'Hello, World (2/5) from wgtvvxbrup!', 'deleted': False, 'created_at': 1707846115472}, {'message_id': '1707846114971:325', 'room_id': 47, 'user_id': 325, 'message': 'Hello, World (1/5) from qniohmhkir!', 'deleted': False, 'created_at': 1707846114971}, {'message_id': '1707846114970:324', 'room_id': 47, 'user_id': 324, 'message': 'Hello, World (1/5) from wgtvvxbrup!', 'deleted': False, 'created_at': 1707846114970}], 'marks': {'324': '1707846116976:325', '325': '1707846116976:325'}}}

"""