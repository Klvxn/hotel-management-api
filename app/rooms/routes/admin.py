from typing import Optional, Any
from uuid import UUID

from fastapi import Depends, Security
from fastapi.routing import APIRouter

from ..models import Review, Room
from ..schema import (
    RoomBase_Pydantic,
    Room_Pydantic_List,
    RoomIn_Pydantic,
    Room_Reviews_Pydantic,
    RoomHistory,
)
from ...auth.utils import authorize_obj_access, get_current_active_user
from ...users.models import Admin


room_router = APIRouter(tags=["Rooms"])


def filter_room_query(query, filters: dict[str, Any]):
    if filters.get("booked") is not None:
        query = query.filter(booked=filters["booked"])
    if filters.get("room_type"):
        query = query.filter(room_type=filters["room_type"])
    return query


@room_router.get("/as_admin", response_model=Room_Pydantic_List)
async def admin_get_rooms(
    current_user: Admin = Security(get_current_active_user, scopes=["admin-read"]),
    booked: Optional[bool] = None,
    room_type: Optional[Room.RoomType] = None,
):
    filters = {"booked": booked, "room_type": room_type}
    query = filter_room_query(Room.all(), filters)
    return await Room_Pydantic_List.from_queryset(query)


@room_router.post("/", response_model=RoomBase_Pydantic, status_code=201)
async def create_room(
    room: RoomIn_Pydantic,
    current_user: Admin = Security(get_current_active_user, scopes=["admin-write"]),
):
    new_room = await Room.create(**room.dict())
    return await RoomBase_Pydantic.from_tortoise_orm(new_room)


@room_router.get("/{room_id}/as_admin", response_model=RoomBase_Pydantic)
async def admin_get_single_room(
    room_id: UUID,
    current_user: Admin = Security(get_current_active_user, scopes=["admin-write"]),
):
    return await RoomBase_Pydantic.from_queryset_single(Room.get(id=room_id))


@room_router.put("/{room_id}", response_model=RoomBase_Pydantic)
async def admin_update_room(
    room_id: UUID,
    room: RoomIn_Pydantic,
    current_user: Admin = Security(get_current_active_user, scopes=["admin-write"]),
):
    await Room.filter(id=room_id).update(**room.dict())
    return await RoomBase_Pydantic.from_queryset_single(Room.get(id=room_id))


@room_router.delete("/{room_id}", response_model={}, status_code=204)
async def admin_delete_room(
    room_id: UUID,
    current_user: Admin = Security(get_current_active_user, scopes=["admin-write"]),
):
    room_obj = await Room.get(id=room_id)
    await room_obj.delete()
    return {}


@room_router.get("/{room_id}/history", response_model=list[RoomHistory])
async def room_reservations_history(
    room_id: UUID,
    current_user: Admin = Security(get_current_active_user, scopes=["admin-read"]),
):
    room = await Room.get(id=room_id).prefetch_related("reservations", "guests")
    return [
        RoomHistory.model_validate(reservation)
        for reservation in await room.reservations
    ]


# --- Review end points ---
@room_router.get("/{room_id}/reviews", response_model=Room_Reviews_Pydantic)
async def get_room_reviews(room_id: UUID):
    return await Room_Reviews_Pydantic.from_queryset_single(Room.get(id=room_id))


@room_router.delete("/reviews/{review_id}", status_code=204)
async def delete_review(
    review_id: int, current_user: Admin = Depends(get_current_active_user)
):
    review_obj = await Review.get(id=review_id).select_related("guest")
    if not current_user.is_admin:
        await authorize_obj_access(review_obj, current_user)
    await review_obj.delete()
    return {}


