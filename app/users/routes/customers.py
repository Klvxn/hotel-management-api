"""
This module contains the API routes for managing customers. It includes endpoints for retrieving a list of customers,
retrieving a single customer, updating a customer's information, updating a customer's active status, deleting a customer,
retrieving a customer's reservations, and retrieving a customer's invoices.
"""

from uuid import UUID

from fastapi import Depends, Security
from fastapi.routing import APIRouter

from ...auth.utils import authorize_obj_access, get_current_active_user
from ...checkout.models import Invoice
from ...schemas import Customer_Pydantic, Invoice_Pydantic, ReservationHistory, UserUpdate
from ...users.models import Admin, BaseUser, Customer


customer_router = APIRouter(prefix="/customers", tags=["Customers"])


@customer_router.get("/", response_model=list[Customer_Pydantic])
async def get_customers(
    current_user: Admin = Security(get_current_active_user, scopes=["admin-read"])
):
    return await Customer_Pydantic.from_queryset(Customer.all())


@customer_router.get("/{customer_uid}", response_model=Customer_Pydantic)
async def get_a_customer(
    customer_uid: UUID,
    current_user: BaseUser = Depends(get_current_active_user)
):
    print("current_user")
    if not current_user.is_admin:
        customer_obj = await Customer.get(uid=customer_uid)
        print(current_user == customer_obj)
        await authorize_obj_access(customer_obj, current_user)    
    return await Customer_Pydantic.from_queryset_single(Customer.get(uid=customer_uid))


@customer_router.put("/{customer_uid}", response_model=Customer_Pydantic)
async def update_customer(
    customer_uid: UUID,
    customer: UserUpdate,
    current_user: Customer = Depends(get_current_active_user)
):
    customer_obj = await Customer.get(uid=customer_uid)
    await authorize_obj_access(customer_obj, current_user)
    await Customer.filter(uid=customer_uid).update(
        **customer.model_dump(exclude={"full_name"})
    )
    return await Customer_Pydantic.from_queryset_single(Customer.get(uid=customer_uid))


@customer_router.patch("/{customer_uid}", response_model=Customer_Pydantic)
async def update_customer_active_status(
    customer_uid: UUID,
    customer: dict[str, bool],
    current_user: Admin = Security(get_current_active_user, scopes=["admin-write"])
):
    await Customer.filter(uid=customer_uid).update(**customer)
    return await Customer_Pydantic.from_queryset_single(Customer.get(uid=customer_uid))


@customer_router.delete("/{customer_uid}", status_code=204)
async def delete_customer(
    customer_uid: UUID, current_user: BaseUser = Depends(get_current_active_user)
):
    customer_obj = await Customer.get(uid=customer_uid)
    if not customer_obj.is_admin:
        await authorize_obj_access(customer_obj, current_user)
    await customer_obj.delete()
    return {}


@customer_router.get("/{customer_uid}/reservations", response_model=list[ReservationHistory])
async def get_customer_reservations(
    customer_uid: UUID,
    current_user: Customer = Depends(get_current_active_user)
):
    customer_obj = await Customer.get(uid=customer_uid)
    if not current_user.is_admin:
        await authorize_obj_access(customer_obj, current_user)
    customer_reservations = await customer_obj.reservations.all()
    return [ReservationHistory.model_validate(reservation) for reservation in customer_reservations]


@customer_router.get("/{customer_uid}/invoices", response_model=list[Invoice_Pydantic])
async def get_customer_invoices(
    customer_uid: UUID, current_user: Customer = Depends(get_current_active_user)
):
    customer_obj = await Customer.get(uid=customer_uid)
    if not current_user.is_admin:
        await authorize_obj_access(customer_obj, current_user)
    return await Invoice_Pydantic.from_queryset(Invoice.filter(customer_email=customer_obj.email))
