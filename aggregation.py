# RDBでJOINする処理を記述する

from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import (
    select,
)
from dataclasses import dataclass

from models import NotificationPushToken, NotificationSettings, RoomMember, User


@dataclass
class NotificationAggregation:

    user_id: int
    notification_type: str
    email: str | None
    tokens: list[str] | None

    @classmethod
    async def notification_in_room(
        cls, session: AsyncSession, room_id: int
    ) -> "list[NotificationAggregation]":
        sql = (
            select(NotificationSettings, NotificationPushToken, User)
            .join(User, User.user_id == NotificationSettings.user_id)
            .join(RoomMember, RoomMember.user_id == NotificationSettings.user_id)
            .join(
                NotificationPushToken,
                and_(
                    NotificationSettings.notification_type == "push",
                    NotificationSettings.user_id == NotificationPushToken.user_id,
                ),
                isouter=True,
            )
            .where(RoomMember.room_id == room_id)
        )
        res = await session.execute(sql)
        ret = {}
        
        for row in res:
            notification = row.NotificationSettings
            if notification.notification_type == "push":
                token = row.NotificationPushToken.token
                if not token:
                    continue
                if notification.user_id not in ret:
                    ret[notification.user_id] = cls(
                        user_id=notification.user_id,
                        notification_type="push",
                        email=None,
                        tokens=[token],
                    )
                else:
                    ret[notification.user_id].tokens.append(token)
            elif notification.notification_type == "email":
                ret[notification.user_id] = cls(
                    user_id=notification.user_id,
                    notification_type="email",
                    email=row.User.email,
                    tokens=None,
                )

        return list(ret.values())
