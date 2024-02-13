# ORMのモデルを定義するファイル
# cf. https://fastapi-users.github.io/fastapi-users/12.1/configuration/databases/sqlalchemy/

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Enum,
    select,
)
from sqlalchemy.orm import relationship, declarative_base

from internal.auth import encrypt_password


Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    password_enc = Column(String(255), nullable=False)

    @classmethod
    async def get_by_id(cls, session: AsyncSession, user_id: int) -> "User | None":
        sql = select(cls).where(cls.user_id == user_id)
        return await session.scalar(sql)

    @classmethod
    async def get_by_username(
        cls, session: AsyncSession, username: str
    ) -> "User | None":
        sql = select(cls).where(cls.username == username)
        return await session.scalar(sql)

    @classmethod
    async def add(
        cls, session: AsyncSession, username: str, email: str, password_enc: str
    ) -> "User":
        user = cls(username=username, email=email, password_enc=password_enc)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @classmethod
    async def authenticate_user(
        cls, session: AsyncSession, username: str, password: str
    ):
        sql = select(cls).where(cls.username == username)
        user = await session.scalar(sql)
        if user is None:
            return None
        if user.password_enc != encrypt_password(password):
            return None
        return user


class Room(Base):
    __tablename__ = "rooms"
    room_id = Column(Integer, primary_key=True)
    room_type = Column(Enum("group", "private"), nullable=False)
    room_name = Column(String(255), nullable=False)

    @classmethod
    async def get_rooms_by_user_id(
        cls, session: AsyncSession, user_id: int
    ) -> list["Room"]:
        sql = (
            select(cls, RoomMember.user_id)
            .join(RoomMember)
            .where(RoomMember.user_id == user_id)
        )
        res = await session.execute(sql)
        return res.scalars()

    @classmethod
    async def get_room_by_id(
        cls, session: AsyncSession, room_id: int, user_id: int
    ) -> "Room | None":
        sql = (
            select(cls)
            .join(RoomMember)
            .where(Room.room_id == room_id, RoomMember.user_id == user_id)
        )
        return await session.scalar(sql)

    @classmethod
    async def add_with_members(
        cls,
        session: AsyncSession,
        room_type: str,
        room_name: str,
        initial_members: list[int],
    ) -> "Room":
        room = cls(room_type=room_type, room_name=room_name)
        session.add(room)
        await session.commit()
        await session.refresh(room)
        for user_id in initial_members:
            session.add(RoomMember(user_id=user_id, room_id=room.room_id))
        await session.commit()
        return room


class RoomMember(Base):
    __tablename__ = "room_members"
    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    room_id = Column(Integer, ForeignKey("rooms.room_id"), primary_key=True)
    user = relationship("User", backref="room_members")
    room = relationship("Room", backref="room_members")

    @classmethod
    async def get_members_by_room_id(
        cls, session: AsyncSession, room_id: int
    ) -> list["User"]:
        sql = select(cls).where(cls.room_id == room_id)
        res = await session.execute(sql)
        return res.scalars()

    @classmethod
    async def add(
        cls, session: AsyncSession, room_id: int, user_ids: list[int]
    ) -> None:
        for user_id in user_ids:
            session.add(RoomMember(user_id=user_id, room_id=room_id))
        await session.commit()


class NotificationPushToken(Base):
    __tablename__ = "notification_push_tokens"
    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    token = Column(String(255), nullable=False, primary_key=True)
    user = relationship("User", backref="notification_push_tokens")

    @classmethod
    async def add(cls, session: AsyncSession, user_id: int, token: str) -> None:
        push_token = cls(user_id=user_id, token=token)
        session.add(push_token)
        await session.commit()


class NotificationSettings(Base):
    __tablename__ = "notification_settings"
    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    notification_type = Column(
        Enum("email", "push", "disabled"), nullable=False, default="disabled"
    )
    user = relationship("User", backref="notification_settings")

    @classmethod
    async def set(
        cls, session: AsyncSession, user_id: int, notification_type: str
    ) -> None:
        settings = cls(user_id=user_id, notification_type=notification_type)
        await session.merge(settings)
        await session.commit()
