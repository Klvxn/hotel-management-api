"""
This module contains the API routes for managing guests. It includes endpoints for retrieving a list of guests,
retrieving a single guest, updating a guest's information, updating a guest's active status, deleting a guest,
retrieving a guest's reservations, and retrieving a guest's invoices.
"""

from fastapi import Depends
from fastapi.routing import APIRouter

from ..models import Guest
from ..schema import (
    Guest_Pydantic,
    UserIn,
    UserUpdate,
)
from ...auth.utils import get_current_active_user, hash_password
from ...checkout.models import Invoice


guest_router = APIRouter(tags=["guests"])


@guest_router.get("/", response_model=Guest_Pydantic)
async def get_guest(current_user: Guest = Depends(get_current_active_user)):
    return await Guest_Pydantic.from_queryset_single(Guest.get(uid=current_user.uid))


@guest_router.post("/sign-up", response_model=Guest_Pydantic, status_code=201)
async def guest_sign_up(guest: UserIn):
    password = guest.password.get_secret_value()
    new_guest = await Guest(**guest.model_dump(exclude={"password_hash"}))
    new_guest.password_hash = hash_password(password)
    await new_guest.save()
    return await Guest_Pydantic.from_tortoise_orm(new_guest)


@guest_router.put("/", response_model=Guest_Pydantic)
async def update_guest(
    guest: UserUpdate, current_user: Guest = Depends(get_current_active_user)
):
    await Guest.filter(uid=current_user.uid).update(
        **guest.model_dump(exclude={"full_name"})
    )
    return await Guest_Pydantic.from_queryset_single(Guest.get(uid=current_user.uid))


@guest_router.delete("/", status_code=204)
async def delete_guest(current_user: Guest = Depends(get_current_active_user)):
    current_user.is_active = False
    await current_user.save()
    return {}


# @guest_router.get("/reservations", response_model=list[ReservationHistory])
# async def get_guest_reservations(
#    current_user: Guest = Depends(get_current_active_user),
# ):
#    guest_reservations = await current_user.reservations.all()
#    return [
#        ReservationHistory.model_validate(reservation)
#        for reservation in guest_reservations
#    ]


# @guest_router.get("/invoices", response_model=list[Invoice_Pydantic])
# async def get_guest_invoices(
#    current_user: Guest = Depends(get_current_active_user),
# ):
#   return await Invoice_Pydantic.from_queryset(
#        Invoice.filter(guest_email=current_user.email)
#    )
