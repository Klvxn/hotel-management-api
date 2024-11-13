from uuid import UUID

from fastapi import Security
from fastapi.routing import APIRouter

from ...auth.utils import authorize_obj_access, get_current_active_user, hash_password
from ...checkout.models import Invoice
from ...users.models import Admin, Guest
from ..schema import (
    Admin_Pydantic,
    Guest_Pydantic,
    UserIn,
    UserUpdate,
)

admin_router = APIRouter(tags=["Admin"])


@admin_router.get("/", response_model=list[Admin_Pydantic])
async def get_all_admins(
    current_user: Admin = Security(get_current_active_user, scopes=["superuser-read"])
):
    return await Admin_Pydantic.from_queryset(Admin.all())


@admin_router.post("/sign-up", response_model=Admin_Pydantic, status_code=201)
async def admin_sign_up(admin: UserIn):
    password = admin.password.get_secret_value()
    admin_obj = await Admin(**admin.model_dump(exclude={"password_hash"}))
    admin_obj.password_hash = hash_password(password)
    await admin_obj.save()
    return await Admin_Pydantic.from_tortoise_orm(admin_obj)


@admin_router.get("/{admin_uid}", response_model=Admin_Pydantic)
async def get_an_admin(
    admin_uid: UUID,
    current_user: Admin = Security(get_current_active_user, scopes=["admin-read"]),
):
    admin_obj = await Admin.get(uid=admin_uid)
    await authorize_obj_access(admin_obj, current_user)
    return await Admin_Pydantic.from_queryset_single(Admin.get(uid=admin_uid))


@admin_router.put("/{admin_uid}", response_model=Admin_Pydantic)
async def update_admin(
    admin_uid: UUID,
    admin: UserUpdate,
    current_user: Admin = Security(get_current_active_user, scopes=["admin-write"]),
):
    admin_obj = await Admin.get(uid=admin_uid)
    await authorize_obj_access(admin_obj, current_user)
    await Admin.filter(uid=admin_uid).update(**admin.model_dump(exclude={"full_name"}))
    return await Admin_Pydantic.from_queryset_single(Admin.get(uid=admin_uid))


@admin_router.patch("/{admin_uid}", response_model=Admin_Pydantic)
async def update_admin_active_status(
    admin_uid: UUID,
    admin: dict[str, bool],
    current_user: Admin = Security(get_current_active_user, scopes=["superuser-write"]),
):
    await Admin.filter(uid=admin_uid).update(**admin)
    return await Admin_Pydantic.from_queryset_single(Admin.get(uid=admin_uid))


@admin_router.delete("/{admin_uid}", status_code=204)
async def delete_admin(
    admin_uid: UUID,
    current_user: Admin = Security(
        get_current_active_user, scopes=["admin-write", "superuser-write"]
    ),
):
    admin_obj = await Admin.get(uid=admin_uid)
    await authorize_obj_access(admin_obj, current_user)
    await admin_obj.delete()
    return {}


# Admin enpoints for managing guest objects
admin_guest_router = APIRouter(prefix="/usrs")


@admin_guest_router.get("/", response_model=list[Guest_Pydantic])
async def get_guests(
    current_user: Admin = Security(get_current_active_user, scopes=["admin-read"])
):
    return await Guest_Pydantic.from_queryset(Guest.all())


@admin_guest_router.get("/{guest_uid}", response_model=Guest_Pydantic)
async def get_a_guest(
    guest_uid: UUID, current_user: Admin = Security(get_current_active_user)
):
    guest_obj = await Guest.get(uid=guest_uid)
    await authorize_obj_access(guest_obj, current_user)
    return await Guest_Pydantic.from_queryset_single(Guest.get(uid=guest_uid))


@admin_guest_router.put("/{guest_uid}", response_model=Guest_Pydantic)
async def update_guest(
    guest_uid: UUID,
    guest: UserUpdate,
    current_user: Admin = Security(get_current_active_user),
):
    await Guest.filter(uid=guest_uid).update(**guest.model_dump(exclude={"full_name"}))
    return await Guest_Pydantic.from_queryset_single(Guest.get(uid=guest_uid))


@admin_guest_router.patch("/{guest_uid}", response_model=Guest_Pydantic)
async def update_guest_active_status(
    guest_uid: UUID,
    guest: dict[str, bool],
    current_user: Admin = Security(get_current_active_user, scopes=["admin-write"]),
):
    await Guest.filter(uid=guest_uid).update(**guest)
    return await Guest_Pydantic.from_queryset_single(Guest.get(uid=guest_uid))


@admin_guest_router.delete("/{guest_uid}", status_code=204)
async def admin_delete_guest(
    guest_uid: UUID, current_user: Admin = Security(get_current_active_user)
):
    guest_obj = await Guest.get(uid=guest_uid)
    await guest_obj.delete()
    return {}


# @admin_guest_router.get("/{guest_uid}/reservations", response_model=list[ReservationHistory])
# async def get_guest_reservations(
#    guest_uid: UUID,
#    current_user: Admin = Security(get_current_active_user)
# ):
#    guest_obj = await Guest.get(uid=guest_uid)
#    await authorize_obj_access(guest_obj, current_user)
#    guest_reservations = await guest_obj.reservations.all()
#    return [ReservationHistory.model_validate(reservation) for reservation in guest_reservations]


# @admin_guest_router.get("/{guest_uid}/invoices", response_model=list[Invoice_Pydantic])
# async def get_guest_invoices(
#   guest_uid: UUID, current_user: Admin = Security(get_current_active_user)
# ):
#    guest_obj = await Guest.get(uid=guest_uid)
#    await authorize_obj_access(guest_obj, current_user)
#    return await Invoice_Pydantic.from_queryset(
#        Invoice.filter(guest_email=guest_obj.email)
#    )


admin_router.include_router(admin_guest_router)
