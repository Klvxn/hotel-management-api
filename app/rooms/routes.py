from datetime import timedelta
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, Security
from fastapi.routing import APIRouter
from tortoise.transactions import in_transaction

from ..auth.utils import authorize_obj_access, get_current_active_user
from ..rooms.models import Review, Room, Reservation
from ..schemas import *
from ..users.models import Customer, Admin, BaseUser


room_router = APIRouter(prefix="/rooms", tags=["Rooms"])
reservation_router = APIRouter(tags=["Reservations"])
review_router = APIRouter(tags=["Reviews"])


# --- Room end points ---

@room_router.get("/", response_model=list[Room_Pydantic])
async def get_rooms(
    booked: Optional[bool] = None, room_type: Optional[Room.RoomType] = None
):
    query = Room.all()
    filters = {}
    if booked is not None:
        filters["booked"] = booked
    if room_type:
        filters["room_type"] = room_type
    query = query.filter(**filters) if filters else query
    return await Room_Pydantic.from_queryset(query)


@room_router.post("/", response_model=Room_Pydantic, status_code=201)
async def create_room(
    room: RoomIn_Pydantic,
    current_user: Admin = Security(get_current_active_user, scopes=["admin-write"])
):
    new_room_obj = await Room.create(**room.dict())
    return await Room_Pydantic.from_tortoise_orm(new_room_obj)


@room_router.get("/{room_id}", response_model=Room_Pydantic)
async def get_single_room(room_id: UUID):
    return await Room_Pydantic.from_queryset_single(Room.get(id=room_id))


@room_router.put("/{room_id}", response_model=Room_Pydantic)
async def update_room(
    room_id: UUID,
    room: RoomIn_Pydantic,
    current_user: Admin = Security(get_current_active_user, scopes=["admin-write"])
):
    await Room.filter(id=room_id).update(**room.dict())
    return await Room_Pydantic.from_queryset_single(Room.get(id=room_id))


@room_router.delete("/{room_id}", status_code=204)
async def delete_room(
    room_id: UUID,
    current_user: Admin = Security(get_current_active_user, scopes=["admin-write"])
):
    room_obj = await Room.get(id=room_id)
    await room_obj.delete()
    return {}


@room_router.get("/{room_id}/reservations", response_model=list[ReservationHistory])
async def room_reservations_history(
    room_id: UUID,
    current_user: Admin = Security(get_current_active_user, scopes=["admin-read"])
):
    room_obj = await Room.get(id=room_id).prefetch_related("reservations")
    return [
        ReservationHistory.model_validate(reservation)
        for reservation in await room_obj.reservations
    ]


@room_router.get("/{room_number}/guests", response_model=RoomGuests)
async def room_guests(
    room_number: int,
    current_user: Admin = Security(get_current_active_user, scopes=["admin-read"])
):
    room = await Room.get_by_room_number(room_number)
    reservations = await Reservation.filter(room=room).select_related("customer")
    return RoomGuests(
        id=room.id,
        room_number=room.room_number,
        customers=[
            UserUpdate(
                first_name=reservation.customer.first_name,
                last_name=reservation.customer.last_name,
                email=reservation.customer.email,
            )
            for reservation in reservations
        ],
    )


# --- Reservation end points ---

@reservation_router.get("/reservations", response_model=list[Reservation_Pydantic])
async def get_all_reservations(
    current_user: Admin = Security(get_current_active_user, scopes=["admin-read"])
):
    return await Reservation_Pydantic.from_queryset(Reservation.all())


@reservation_router.post("/reservations", response_model=Reservation_Pydantic, status_code=201)
async def make_reservation(
    reservation: ReservationIn,
    current_user: BaseUser = Security(get_current_active_user)
):
    room_number = reservation.room_number
    room = await Room.get_by_room_number(room_number)
    check_in = reservation.check_in_date.replace(second=0, microsecond=0, tzinfo=None)
    check_out = reservation.check_out_date.replace(second=0, microsecond=0, tzinfo=None)
    last_reservation = await Reservation.filter(room_id=room.id, customer_checked_out=False).first()
    if last_reservation:
        last_reservation_check_out = last_reservation.check_out_date.replace(tzinfo=None)
        if room.booked or check_in <= last_reservation_check_out + timedelta(hours=2):
            raise HTTPException(
                400,
                f"Room is currently unavailable between {check_in} and {check_out}. Adjust your check in and check out dates",
            )
    if not check_in < check_out or datetime.now() > check_in:
        raise HTTPException(400, "Invalid check in and check out dates")
    reservation = reservation.model_dump(exclude={"room_number"})
    async with in_transaction():
        new_reservation = await Reservation.create(
            **reservation, room_id=room.id, customer_id=current_user.uid
        )
        room.booked = True
        await room.save()
        return await Reservation_Pydantic.from_tortoise_orm(new_reservation)


@reservation_router.get("/reservations/{reservation_id}", response_model=Reservation_Pydantic)
async def get_single_reservation(
    reservation_id: UUID, current_user: BaseUser = Security(get_current_active_user)
):
    reservation_obj = await Reservation.get(id=reservation_id).select_related("customer")
    if not current_user.is_admin:
        await authorize_obj_access(reservation_obj, current_user)
    return await Reservation_Pydantic.from_queryset_single(Reservation.get(id=reservation_id))


@reservation_router.put("/reservations/{reservation_id}", response_model=Reservation_Pydantic)
async def update_reservation(
    reservation_id: UUID,
    reservation: ReservationUpdate,
    current_user: Customer = Security(get_current_active_user)
):
    room_number = reservation.room_number
    room = await Room.get_by_room_number(room_number)
    reservation_obj = await Reservation.get(id=reservation_id).select_related("customer")
    await authorize_obj_access(reservation_obj, current_user)
    await Reservation.filter(id=reservation_id).update(
        **reservation.model_dump(exclude={"room_number"}),
        customer=await reservation_obj.customer,
        room=room
    )
    return await Reservation_Pydantic.from_queryset_single(Reservation.get(id=reservation_id))


@reservation_router.put("/reservations/{reservation_id}/checked_out", response_model=dict)
async def update_customer_checked_out(
    reservation_id: UUID,
    data: dict[str, bool],
    current_user: Admin = Security(get_current_active_user, scopes=["admin-write"])
):
    reservation = await Reservation.get(id=reservation_id)
    await reservation.update_from_dict(**data).save()
    return {"detail": "Reservation has been updated"}


@reservation_router.delete("/reservations/{reservation_id}", status_code=204)
async def delete_reservation(
    reservation_id: UUID,
    current_user: BaseUser = Security(get_current_active_user)
):
    reservation_obj = await Reservation.get(id=reservation_id).prefetch_related("room", "customer")
    if not current_user.is_admin:
        await authorize_obj_access(reservation_obj, current_user)
    async with in_transaction():
        room = reservation_obj.room
        await room.update_from_dict({"booked": False}).save()
        await reservation_obj.delete()
        return {}


# --- Review end points ---

@review_router.get("/reviews", response_model=list[Review_Pydantic])
async def get_all_reviews():
    return await Review_Pydantic.from_queryset(Review.all())


@review_router.post("/reviews/{room_number}", response_model=Review_Pydantic, status_code=201)
async def add_review(
    room_number: int,
    review: ReviewIn,
    current_user: BaseUser = Security(get_current_active_user)
):
    room = await Room.get_by_room_number(room_number)
    reservation = await Reservation.filter(room_id=room.id, customer_id=current_user.uid).first()
    if not reservation:
        raise HTTPException(
            400, "You must stay in a room at least 24 hours to leave a review"
        )
    new_review = await Review.create(
        **review.model_dump(), room_id=room.id, customer_id=current_user.uid
    )
    return await Review_Pydantic.from_tortoise_orm(new_review)


@review_router.get("/reviews/{reviews_id}", response_model=Reservation_Pydantic)
async def get_single_review(review_id: int):
    return await Review_Pydantic.from_queryset_single(Review.get(id=review_id))


@review_router.put("/reviews/{review_id}", response_model=Review_Pydantic)
async def update_review(
    review_id: int,
    review: ReviewIn,
    current_user: Customer = Security(get_current_active_user)
):
    review_obj = await Review.get(id=review_id).select_related("customer")
    await authorize_obj_access(review_obj, current_user)
    await Review.filter(id=review_id).update(**review.model_dump())
    return await Review_Pydantic.from_queryset_single(Review.get(id=review_id))


@review_router.delete("/reviews/{review_id}", status_code=204)
async def delete_review(
    review_id: int, current_user: BaseUser = Security(get_current_active_user)
):
    review_obj = await Review.get(id=review_id).select_related("customer")
    if not current_user.is_admin:
        await authorize_obj_access(review_obj, current_user)
    await review_obj.delete()
    return {}
