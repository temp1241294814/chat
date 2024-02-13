from pydantic import BaseModel
from typing import Literal



class User(BaseModel):
    user_id: int
    username: str
    email: str
    password: str


class Room(BaseModel):
    room_id: int
    room_type: Literal["group", "private"]
    room_name: str


class NotificationSettings(BaseModel):
    user_id: int
    notification_type: Literal["email", "push", "disabled"]


class NotificationPushToken(BaseModel):
    user_id: int
    token: str


class Message(BaseModel):
    message_id: int
    room_id: int
    user_id: int
    message: str
    created_at: str


class LoginRequest(BaseModel):
    username: str
    password: str


class CreateUserRequest(BaseModel):
    username: str
    email: str
    password: str


class CreateUserResponse(BaseModel):
    user_id: int
    username: str
    email: str

    class Config:
        orm_mode = True


class NotificationSettingsRequest(BaseModel):
    notification_type: Literal["email", "push", "disabled"]


class NotificationPushTokenRequest(BaseModel):
    user_id: int
    token: str


class CreateRoomRequest(BaseModel):
    room_type: Literal["group", "private"]
    room_name: str
    initial_members: list[int]


class ListRoomResponse(BaseModel):
    rooms: list[Room]


class CreateRoomResponse(BaseModel):
    room_id: int
    room_type: Literal["group", "private"]
    room_name: str


class AddUserToRoomRequest(BaseModel):
    room_id: int
    user_ids: list[int]


class AddNotificationPushTokenRequest(BaseModel):
    user_id: int
    token: str


class MessageLog(BaseModel):
    message_id: str
    room_id: int
    user_id: int
    message: str
    deleted: bool
    created_at: int  # milliseconds


class InitialData(BaseModel):
    messages: list[MessageLog]
    marks: dict[int, str]


class ClientEvent(BaseModel):
    """Event from client to server"""

    event_type: Literal["post", "delete", "mark"]
    message: str | None = None
    message_id: str | None = None


class ServerEvent(BaseModel):
    """Event from server to client"""

    session_id: str
    event_type: Literal["post", "delete", "mark", "init"]
    message: MessageLog | None = None
    message_id: str | None = None
    user_id: int | None = None
    initial_data: InitialData | None = None
