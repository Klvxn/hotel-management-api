from uuid import UUID

from fastapi.routing import APIRouter
from tortoise.transactions import in_transaction

from ..models import Reservation
from ..schema import Reservation_Pydantic, Reservation_Pydantic_List


reservation_router = APIRouter(tags=["Reservations"])


@reservation_router.get("/", response_model=Reservation_Pydantic_List)
async def get_all_reservations():
    return await Reservation_Pydantic_List.from_queryset(Reservation.all())


@reservation_router.get("/{reservation_id}", response_model=Reservation_Pydantic)
async def get_single_reservation(reservation_id: UUID):
    return await Reservation_Pydantic.from_queryset_single(Reservation.get(id=reservation_id))


@reservation_router.put("/{reservation_id}/checked_out", response_model=dict[str, str])
async def update_reservation_status(reservation_id: UUID, data: dict[str, bool]):
    reservation = await Reservation.get(id=reservation_id)
    await reservation.update_from_dict(data).save()
    return {"detail": "Reservation has been updated"}


@reservation_router.delete("/{reservation_id}", response_model={}, status_code=204)
async def delete_reservation(reservation_id: UUID):
    reservation = await Reservation.get(id=reservation_id).prefetch_related("room")
    async with in_transaction():
        reserved_rooms = reservation.rooms
        for room in reserved_rooms:
            room.booked = False
        await reservation.bulk_update(reserved_rooms, "booked")
        await reservation.delete()
        return {}
