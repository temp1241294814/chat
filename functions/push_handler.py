# https://firebase.google.com/docs/cloud-messaging/send-message?hl=ja

import firebase_admin
from firebase_admin import messaging
import base64
import json
import functions_framework

firebase_admin.initialize_app()


@functions_framework.http
def handle_push(request):
    request_json = request.get_json()
    data = json.loads(base64.b64decode(request_json["message"]["data"]).decode("utf-8"))
    tokens = data.get("tokens")
    # データメッセージとして送信
    message = messaging.MulticastMessage(
        data={
            "room": data.get("room"),
            "user": data.get("user"),
            "message": data.get("message"),
        },
        token=tokens,
    )
    messaging.send_multicast(message)
    return "ok", 200
