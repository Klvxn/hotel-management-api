from uuid import UUID

from fastapi import Security
from fastapi.routing import APIRouter

from ...schemas import Admin_Pydantic, UserIn, UserUpdate
from ...users.models import Admin
from ...auth.utils import authorize_obj_access, get_current_active_user, hash_password


admin_router = APIRouter(prefix="/org/private/admins", tags=["Admin"])


@admin_router.get("/", response_model=list[Admin_Pydantic])
async def get_all_admins(
    current_user: Admin = Security(get_current_active_user, scopes=["superuser-read"])
):
    return await Admin_Pydantic.from_queryset(Admin.all())


@admin_router.post("/sign-up", response_model=Admin_Pydantic, status_code=201)
async def sign_up_admins(admin: UserIn):
    password = admin.password.get_secret_value()
    admin_obj = await Admin(**admin.model_dump(exclude={"password_hash"}))
    admin_obj.password_hash = hash_password(password)
    await admin_obj.save()
    return await Admin_Pydantic.from_tortoise_orm(admin_obj)


@admin_router.get("/{admin_uid}", response_model=Admin_Pydantic)
async def get_an_admin(
    admin_uid: UUID,
    current_user: Admin = Security(get_current_active_user, scopes=["admin-read"])
):
    admin_obj = await Admin.get(uid=admin_uid)
    await authorize_obj_access(admin_obj, current_user)
    return await Admin_Pydantic.from_queryset_single(Admin.get(uid=admin_uid))


@admin_router.put("/{admin_uid}", response_model=Admin_Pydantic)
async def update_admin(
    admin_uid: UUID,
    admin: UserUpdate,
    current_user: Admin = Security(get_current_active_user, scopes=["admin-write"])
):
    admin_obj = await Admin.get(uid=admin_uid)
    await authorize_obj_access(admin_obj, current_user)
    await Admin.filter(uid=admin_uid).update(**admin.model_dump(exclude={"full_name"}))
    return await Admin_Pydantic.from_queryset_single(Admin.get(uid=admin_uid))


@admin_router.patch("/{admin_uid}", response_model=Admin_Pydantic)
async def update_admin_active_status(
    admin_uid: UUID,
    admin: dict[str, bool],
    current_user: Admin = Security(get_current_active_user, scopes=["superuser-write"])
):
    await Admin.filter(uid=admin_uid).update(**admin)
    return await Admin_Pydantic.from_queryset_single(Admin.get(uid=admin_uid))


@admin_router.delete("/{admin_uid}", status_code=204)
async def delete_admin(
    admin_uid: UUID,
    current_user: Admin = Security(
        get_current_active_user, scopes=["admin-write", "superuser-write"]
    )
):
    admin_obj = await Admin.get(uid=admin_uid)
    await authorize_obj_access(admin_obj, current_user)
    await admin_obj.delete()
    return {}
