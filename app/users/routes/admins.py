from uuid import UUID

from fastapi import Security
from fastapi.routing import APIRouter

from ...users.models import Admin, Admin_Pydantic, AdminIn_Pydantic, AdminUpdate
from ...auth.utils import (
    authorize_admin_access,
    get_current_user,
    hash_password,
)


admin_router = APIRouter(prefix="/org/private/admins", tags=["Admin"])


@admin_router.get("/", response_model=list[Admin_Pydantic])
async def get_all_admins(
    current_user: Admin = Security(get_current_user, scopes=["superuser-read"])
):
    return await Admin_Pydantic.from_queryset(Admin.all())


@admin_router.post("/sign-up", response_model=Admin_Pydantic, status_code=201)
async def sign_up_admins(admin: AdminIn_Pydantic):
    password = admin.dict().pop("password_hash")
    admin_obj = await Admin(**admin.dict(exclude=("password_hash",)))
    admin_obj.password_hash = hash_password(password)
    await admin_obj.save()
    return await Admin_Pydantic.from_tortoise_orm(admin_obj)


@admin_router.get("/{admin_uid}", response_model=Admin_Pydantic)
async def get_an_admin(
    admin_uid: UUID,
    current_user: Admin = Security(
        get_current_user, scopes=["admin-read", "superuser-read"]
    ),
):
    await authorize_admin_access(admin_uid, current_user)
    return await Admin_Pydantic.from_queryset_single(Admin.get(uid=admin_uid))


@admin_router.put("/{admin_uid}", response_model=Admin_Pydantic)
async def update_admin(
    admin_uid: UUID,
    admin: AdminUpdate,
    current_user: Admin = Security(get_current_user, scopes=["admin-write"]),
):
    await authorize_admin_access(admin_uid, current_user)
    await Admin.filter(uid=admin_uid).update(**admin.dict(exclude=("full_name",)))
    return await Admin_Pydantic.from_queryset_single(Admin.get(uid=admin_uid))


@admin_router.delete("/{admin_uid}", status_code=204)
async def delete_admin(
    admin_uid: UUID,
    current_user: Admin = Security(
        get_current_user, scopes=["admin-write", "superuser-write"]
    ),
):
    admin_obj = await Admin.get(uid=admin_uid)
    await authorize_admin_access(admin_uid, current_user)
    await admin_obj.delete()
    return {}
