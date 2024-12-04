import yagmail
from datetime import datetime
from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.background import BackgroundTasks
from fastapi.routing import APIRouter
from tortoise.transactions import in_transaction

from ..models import Reservation
from ..schema import Reservation_Pydantic, ReservationIn
from ...config import settings
from ...auth.utils import get_current_active_user
from ...rooms.models import Room, RoomAvailability
from ...users.models import Guest


reservation_router = APIRouter(tags=["Reservations"])


def normalize_date(date: datetime):
    return date.replace(second=0, microsecond=0, tzinfo=None)


def email_new_reservation(current_user: Guest, reservation: Reservation):
    with yagmail.SMTP(settings.email_user, settings.email_password) as yag:
        yag.send(
            to=current_user.email,
            subject="New Reservation, Welcome!",
            contents=f"""
            Hi {current_user.first_name},

            Thank you for booking a reservation at our hotel. 
            We are excited to welcome you to our establishment and hope you enjoy your stay.

            Your reservation details are as follows:

            Room Numbers: #{reservation.rooms}
            # Room Type: room.room_type
            Cost Per Night: $room.price:.2f
            Check-In Date: {reservation.check_in_date.date()}
            Check-Out Date: {reservation.check_out_date.date()}
            Total Due: ${reservation.reservation_due:.2f}

            If you have any questions or concerns, please don't hesitate to contact us.

            Best regards,
            Management.
            """,
        )
        return


@reservation_router.get("/", response_model=list[Reservation_Pydantic])
async def guest_reservations(current_user: Guest = Depends(get_current_active_user)):
    # No need to explicitly call the `authorize_obj_access` helper function as
    # reservations are filtered based on `current_user` dependency
    return await Reservation_Pydantic.from_queryset(
        Reservation.filter(guest=current_user)
    )


@reservation_router.post("/", response_model=Reservation_Pydantic, status_code=201)
async def make_reservation(
    reservation: ReservationIn,
    background_task: BackgroundTasks,
    current_user: Guest = Depends(get_current_active_user),
):
    # Check for room availability between check-in and check-out dates
    for room_number in reservation.room_numbers:
        check_in = normalize_date(reservation.check_in_date).date()
        check_out = normalize_date(reservation.check_out_date).date()
        if await RoomAvailability.check_room_is_available(
            room_number, check_in, check_out
        ):
            raise HTTPException(
                400, f"Room {room_number} is not available within the selected dates"
            )

    # Open a transaction to perform multiple db operations
    async with in_transaction("default"):
        # Create new reservation
        new_reservation = await Reservation.create(
            guest=current_user,
            check_in_date=reservation.check_in_date,
            check_out_date=reservation.check_out_date,
            occupants=reservation.occupants,
        )

        # Link the reservation with rooms and create RoomAvailability record
        for room_number in reservation.room_numbers:
            room = await Room.get_by_room_number(room_number)
            await new_reservation.rooms.add(room)

            await RoomAvailability.create(
                room=room,
                reservation=new_reservation,
                start_date=new_reservation.check_in_date.date(),
                end_date=new_reservation.check_out_date.date(),
                booked=True,
            )

        # Send new reservation mail
        background_task.add_task(email_new_reservation, current_user, new_reservation)

        return await Reservation_Pydantic.from_tortoise_orm(new_reservation)


@reservation_router.get("/{reservation_id}", response_model=Reservation_Pydantic)
async def get_single_reservation(
    reservation_id: UUID, current_user: Guest = Depends(get_current_active_user)
):
    return await Reservation_Pydantic.from_queryset_single(
        Reservation.get(id=reservation_id, guest=current_user)
    )


@reservation_router.put("/{reservation_id}", response_model=Reservation_Pydantic)
async def update_reservation(
    reservation_id: UUID,
    reservation: ReservationIn,
    current_user: Guest = Depends(get_current_active_user),
):
    reservation_obj = await Reservation.get(id=reservation_id, guest=current_user)
    await reservation_obj.update_from_dict(
        **reservation.model_dump(exclude={"room_numbers"})
    )
    await reservation_obj.save()
    rooms = [
        await Room.get_by_room_number(room_number)
        for room_number in reservation.room_numbers
    ]
    await reservation_obj.rooms.add(rooms)

    return await Reservation_Pydantic.from_tortoise_orm(reservation_obj)
