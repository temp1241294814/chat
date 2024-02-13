from datetime import datetime
from google.cloud import firestore

from schema import MessageLog

firestore_client = firestore.AsyncClient()


class MessageStore:

    def __init__(self, room_id: int, user_id: int):
        self.room_id = room_id
        self.user_id = user_id

    async def post_message(self, message: str):
        """Firestoreにメッセージを保存する"""
        ts = int(datetime.now().timestamp() * 1000)
        room_path = firestore_client.collection("chatHistory").document(
            str(self.room_id)
        )
        key = f"{ts}:{self.user_id}"
        log = MessageLog(
            message_id=key,
            room_id=self.room_id,
            user_id=self.user_id,
            message=message,
            deleted=False,
            created_at=ts,
        )
        await room_path.collection("messages").document(key).set(log.model_dump())
        return log

    async def delete_message(self, message_id: str):
        """Firestoreからメッセージを削除する"""
        path = (
            firestore_client.collection("chatHistory")
            .document(str(self.room_id))
            .collection("messages")
            .document(message_id)
        )
        res = await path.get()
        if res and res.get("user_id") == self.user_id:
            await path.update({"deleted": True})
        return res

    async def get_history(self, count: int) -> list[MessageLog]:
        """Firestoreからメッセージの履歴を取得する(最新から指定数)"""
        room_path = (
            firestore_client.collection("chatHistory")
            .document(str(self.room_id))
            .collection("messages")
        )
        query = room_path.order_by(
            "message_id", direction=firestore.Query.DESCENDING
        ).limit(count)
        r = await query.get()
        return [MessageLog.model_validate(doc.to_dict()) for doc in r]
