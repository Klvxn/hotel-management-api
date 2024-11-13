from datetime import datetime
from typing import Optional, Any
from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.routing import APIRouter

from ..models import Review, Room
from ..schema import (
    RoomBase_Pydantic,
    Room_Pydantic_List,
    Room_Reviews_Pydantic,
    Review_Pydantic,
    ReviewIn,
)
from ...auth.utils import authorize_obj_access, get_current_active_user
from ...users.models import Guest


room_router = APIRouter(tags=["Rooms"])


def filter_room_query(query, filters: dict[str, Any]):
    if filters.get("booked") is not None:
        query = query.filter(booked=filters["booked"])
    if filters.get("room_type"):
        query = query.filter(room_type=filters["room_type"])
    return query


@room_router.get("/", response_model=Room_Pydantic_List)
async def get_rooms(
    booked: Optional[bool] = None, room_type: Optional[Room.RoomType] = None
):
    filters = {"booked": booked, "room_type": room_type}
    query = filter_room_query(Room.all(), filters)
    return await Room_Pydantic_List.from_queryset(query)


@room_router.get("/{room_id}", response_model=RoomBase_Pydantic)
async def get_single_room(room_id: UUID):
    return await RoomBase_Pydantic.from_tortoise_orm(await Room.get(id=room_id))


# Review end points
@room_router.get("/{room_number}/reviews", response_model=Room_Reviews_Pydantic)
async def get_room_reviews(room_number: int):
    return await Room_Reviews_Pydantic.from_queryset_single(
        Room.get_by_room_number(room_number)
    )


@room_router.post(
    "/{room_number}/reviews", response_model=Review_Pydantic, status_code=201
)
async def add_review(
    room_number: int,
    review: ReviewIn,
    current_user: Guest = Depends(get_current_active_user),
):
    now = datetime.now()
    guest_reserv = current_user.reservations.filter(
        room__room_number=room_number, check_out_date__lt=now
    ).exists()
    print(guest_reserv)
    if not guest_reserv:
        raise HTTPException(
            400, "You must stay in a room at least 24 hours to leave a review"
        )
    new_review = await Review.create(
        **review.model_dump(), room__room_number=room_number, guest=current_user
    )
    return await Review_Pydantic.from_tortoise_orm(new_review)


@room_router.get("/{room_number}/reviews/{reviews_id}", response_model=Review_Pydantic)
async def get_room_review(room_number: int, review_id: int):
    return await Review_Pydantic.from_queryset_single(
        Review.get(room__room_number=room_number, id=review_id)
    )


@room_router.put("/{room_number}/reviews/{review_id}", response_model=Review_Pydantic)
async def update_review(
    room_number: int,
    review_id: int,
    review: ReviewIn,
    current_user: Guest = Depends(get_current_active_user),
):
    review_obj = await Review.get(id=review_id, room__room_number=room_number)
    await authorize_obj_access(review_obj, current_user)
    await Review.filter(id=review_id).update(**review.model_dump())
    return await Review_Pydantic.from_tortoise_orm(review_obj)


@room_router.delete("/{room_number}/reviews/{review_id}", status_code=204)
async def delete_review(
    room_number: int,
    review_id: int,
    current_user: Guest = Depends(get_current_active_user),
):
    review_obj = await Review.get(id=review_id, room__room_number=room_number)
    await authorize_obj_access(review_obj, current_user)
    await review_obj.delete()
    return {}
