from uuid import UUID

from fastapi import Security
from fastapi.routing import APIRouter

from ...users.models import Admin, BaseUser, Customer
from ...schemas import Customer_Pydantic, ReservationHistory, UserUpdate
from ...auth.utils import get_current_active_user, authorize_customer_access

customer_router = APIRouter(prefix="/customers", tags=["Customers"])


@customer_router.get("/", response_model=list[Customer_Pydantic])
async def get_customers(
    current_user: Admin = Security(get_current_active_user, scopes=["admin-read"])
):
    return await Customer_Pydantic.from_queryset(Customer.all())


@customer_router.get("/{customer_uid}", response_model=Customer_Pydantic)
async def get_a_customer(
    customer_uid: UUID,
    current_user: BaseUser = Security(
        get_current_active_user, scopes=["admin-read", "customer-read"]
    ),
):
    await authorize_customer_access(customer_uid, current_user=current_user)
    return await Customer_Pydantic.from_queryset_single(Customer.get(uid=customer_uid))


@customer_router.put("/{customer_uid}", response_model=Customer_Pydantic)
async def update_customer(
    customer_uid: UUID,
    customer: UserUpdate,
    current_user: Customer = Security(
        get_current_active_user, scopes=["customer-write"]
    ),
):
    await authorize_customer_access(
        customer_uid, current_user=current_user, allow_admin=False
    )
    await Customer.filter(uid=customer_uid).update(
        **customer.model_dump(exclude={"full_name"})
    )
    return await Customer_Pydantic.from_queryset_single(Customer.get(uid=customer_uid))


@customer_router.delete("/{customer_uid}", status_code=204)
async def delete_customer(
    customer_uid: UUID,
    current_user: BaseUser = Security(
        get_current_active_user, scopes=["admin-write", "customer-write"]
    ),
):
    customer_obj = await Customer.get(uid=customer_uid)
    await authorize_customer_access(customer_uid, current_user)
    await customer_obj.delete()
    return {}


@customer_router.get("/{customer_uid}/reservations", response_model=list[ReservationHistory])
async def customer_reservations_history(
    customer_uid: UUID,
    current_user: BaseUser = Security(
        get_current_active_user, scopes=["admin-read", "customer-read"]
    ),
):
    customer_obj = await Customer.get(uid=customer_uid)
    await authorize_customer_access(customer_uid, current_user=current_user)
    customer_reservations = await customer_obj.reservations.all()
    return [ReservationHistory.model_validate(reservation) for reservation in customer_reservations]
