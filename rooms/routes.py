from uuid import UUID

from fastapi import HTTPException, Security
from fastapi.routing import APIRouter
from tortoise.transactions import in_transaction

from auth.utils import get_current_user
from rooms.models import (
    Room,
    Room_Pydantic,
    RoomIn_Pydantic,
    Reservation,
    Reservation_Pydantic,
)
from schemas import ReservationSchema, ReservationUpdateSchema
from users.models import Customer, Admin, BaseUser


room_router = APIRouter(prefix="/rooms", tags=["Rooms"])
reservation_router = APIRouter(tags=["Reservations"])


@room_router.get("/", response_model=list[Room_Pydantic])
async def get_rooms(booked: bool | None = None):
    if booked:
        return await Room_Pydantic.from_queryset(Room.filter(booked=booked).all())
    return await Room_Pydantic.from_queryset(Room.all())


@room_router.post("/", response_model=Room_Pydantic, status_code=201)
async def create_room(
    room: RoomIn_Pydantic,
    current_user: Admin = Security(get_current_user, scopes=["admin-write"]),
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
    current_user: Admin = Security(get_current_user, scopes=["admin-write"]),
):
    await Room.filter(id=room_id).update(**room.dict())
    return await Room_Pydantic.from_queryset_single(Room.get(id=room_id))


@room_router.delete("/{room_id}", status_code=204)
async def delete_room(
    room_id: UUID,
    current_user: Admin = Security(get_current_user, scopes=["admin-write"]),
):
    room_obj = await Room.get(id=room_id)
    await room_obj.delete()
    return {}


@room_router.get("/{room_id}/reservations", response_model=list[ReservationSchema])
async def get_room_reservations(
    room_id: UUID,
    current_user: Admin = Security(get_current_user, scopes=["admin-read"]),
):
    room_obj = await Room.get(id=room_id)
    return (
        await Reservation.filter(room=room_obj)
        .all()
        .values(
            "check_in_date",
            "check_out_date",
            "occupants",
            reservation_id="id",
            room_number="room__room_number",
            customer_email="customer__email",
        )
    )


@reservation_router.get("/reservations", response_model=list[Reservation_Pydantic])
async def get_all_reservations(
    current_user: Admin = Security(get_current_user, scopes=["admin-read"])
):
    return await Reservation_Pydantic.from_queryset(Reservation.all())


@reservation_router.post(
    "/reservations", response_model=Reservation_Pydantic, status_code=201
)
async def make_reservation(
    reservation: ReservationSchema,
    current_user: BaseUser = Security(get_current_user, scopes=["customer-write"]),
):
    room_number = reservation.room_number
    room = await Room.get_by_room_number(room_number)
    if room.booked:
        raise HTTPException(400, "Room has already been booked")
    check_in = reservation.check_in_date
    check_out = reservation.check_out_date
    if check_in >= check_out:
        raise HTTPException(400, "Invalid check in and check out dates")
    reservation = reservation.model_dump(exclude={"room_number"}, by_alias=True)
    async with in_transaction():
        new_reservation = await Reservation.create(
            **reservation, room_id=room.id, customer_id=current_user.uid
        )
        room.booked = True
        await room.save()
        return await Reservation_Pydantic.from_tortoise_orm(new_reservation)


@reservation_router.get(
    "/reservations/{reservation_id}", response_model=Reservation_Pydantic
)
async def get_single_reservation(
    reservation_id: UUID,
    current_user: BaseUser = Security(
        get_current_user, scopes=["admin-read", "customer-read"]
    ),
):
    reservation_obj = await Reservation.get(id=reservation_id)
    if not current_user.is_admin:
        try:
            assert current_user == await reservation_obj.customer
        except AssertionError:
            raise HTTPException(403, "Unauthorized access")
    return await Reservation_Pydantic.from_queryset_single(
        Reservation.get(id=reservation_id)
    )


@reservation_router.put(
    "/reservations/{reservation_id}", response_model=Reservation_Pydantic
)
async def update_reservation(
    reservation_id: UUID,
    reservation: ReservationUpdateSchema,
    current_user: Customer = Security(get_current_user, scopes=["customer-write"]),
):
    room_number = reservation.room_number
    room = await Room.get_by_room_number(room_number)
    reservation_obj = await Reservation.get(id=reservation_id)
    try:
        assert current_user == await reservation_obj.customer
    except AssertionError:
        raise HTTPException(403, "Unauthorized access")
    await Reservation.filter(id=reservation_id).update(
        **reservation.model_dump(exclude={"room_number"}),
        customer=await reservation_obj.customer,
        room=room
    )
    return await Reservation_Pydantic.from_queryset_single(
        Reservation.get(id=reservation_id)
    )


@reservation_router.delete("/reservations/{reservation_id}", status_code=204)
async def delete_reservation(
    reservation_id: UUID,
    current_user: BaseUser = Security(
        get_current_user, scopes=["admin-write", "customer-write"]
    ),
):
    reservation_obj = await Reservation.get(id=reservation_id)
    if not current_user.is_admin:
        try:
            assert current_user == await reservation_obj.customer
        except AssertionError:
            raise HTTPException(403, "Unauthorized access")
    async with in_transaction():
        room = await reservation_obj.room
        await room.update_from_dict({"booked": False}).save()
        await reservation_obj.delete()
        return {}
