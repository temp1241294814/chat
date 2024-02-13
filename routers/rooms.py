from fastapi import APIRouter, HTTPException
from models import Room, RoomMember
from dependencies import CurrentUser, RDBSession
import schema
from schema import (
    AddUserToRoomRequest,
    CreateRoomRequest,
    CreateRoomResponse,
    ListRoomResponse,
)

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("")
async def list_room(db: RDBSession, current_user_id: CurrentUser):
    """ユーザーが参加しているルーム一覧を取得"""
    rooms = await Room.get_rooms_by_user_id(db, current_user_id)
    return ListRoomResponse(
        rooms=[
            schema.Room(
                room_id=room.room_id, room_type=room.room_type, room_name=room.room_name
            )
            for room in rooms
        ]
    )


@router.post("")
async def create_room(
    body: CreateRoomRequest, db: RDBSession, current_user_id: CurrentUser
):
    """ルームを作成"""
    if current_user_id not in body.initial_members:
        # 自分が初期メンバーに含まれていない場合はエラー
        raise HTTPException(
            status_code=400, detail="You must be in the initial members"
        )
    if body.room_type == "private" and len(body.initial_members) != 2:
        # 1on1の場合は初期メンバーが2人でなければエラー
        raise HTTPException(
            status_code=400, detail="Invalid number of initial members for private room"
        )
    room = await Room.add_with_members(
        db, body.room_type, body.room_name, body.initial_members
    )
    return CreateRoomResponse(
        room_id=room.room_id, room_type=room.room_type, room_name=room.room_name
    )


@router.post("/{room_id}/members")
async def add_room_members(
    room_id: int,
    body: AddUserToRoomRequest,
    db: RDBSession,
    current_user_id: CurrentUser,
):
    """ルームにメンバーを追加"""
    room = await Room.get_room_by_id(db, room_id, current_user_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    if room.room_type == "private":
        # プライベートルームの場合はエラー
        raise HTTPException(
            status_code=400, detail="You cannot add members to a private room"
        )
    await RoomMember.add(db, room_id, body.user_ids)


@router.get("/{room_id}/members")
async def get_room_members(room_id: int, db: RDBSession, current_user_id: CurrentUser):
    """ルームのメンバー一覧を取得"""
    room = await Room.get_room_by_id(db, room_id, current_user_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    members = await RoomMember.get_members_by_room_id(db, room_id)
    return [member.user_id for member in members]
