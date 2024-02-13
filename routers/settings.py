from fastapi import APIRouter
from models import (
    NotificationPushToken,
    NotificationSettings,
)
from dependencies import CurrentUser, RDBSession
from schema import (
    NotificationPushTokenRequest,
    NotificationSettingsRequest,
)

router = APIRouter(prefix="/settings", tags=["settings"])


@router.post("/notification")
async def notification_settings(
    body: NotificationSettingsRequest, db: RDBSession, current_user_id: CurrentUser
):
    """通知設定"""
    await NotificationSettings.set(db, current_user_id, body.notification_type)
    return {"message": "Notification settings updated"}


@router.post("/notification/push-token")
async def notification_push_token(
    body: NotificationPushTokenRequest, db: RDBSession, current_user_id: CurrentUser
):
    """Push通知のトークンを登録"""
    await NotificationPushToken.add(db, current_user_id, body.token)
    return {"message": "Push token updated"}
