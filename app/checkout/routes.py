from typing import Optional
from uuid import UUID

import stripe
from fastapi import APIRouter, HTTPException, Security
from fastapi.responses import RedirectResponse

from ..users.models import Admin, BaseUser, Customer
from .models import Invoice, PaidStatus
from ..auth.utils import authorize_obj_access, get_current_active_user
from ..config import settings
from ..rooms.models import Reservation
from ..schemas import Invoice_Pydantic, InvoiceUpdate


invoice_router = APIRouter(prefix="/invoices", tags=["Invoices"])
checkout_router = APIRouter(prefix="/checkout", tags=["Checkout"])

stripe.api_key = settings.stripe_secret_key


@invoice_router.get("/", response_model=list[Invoice_Pydantic])
async def get_invoices(
    status: Optional[PaidStatus] = None,
    customer_email: Optional[str] = None,
    # current_user: Admin = Security(get_current_active_user, scopes=["admin-read"])
):
    query = Invoice.all()
    if status:
        query = query.filter(status=status)
    if customer_email:
        query = query.filter(customer_email=customer_email)
    return await Invoice_Pydantic.from_queryset(query)


@invoice_router.get("/{invoice_id}", response_model=Invoice_Pydantic)
async def get_invoice(
    invoice_id: UUID, 
    current_user: BaseUser = Security(get_current_active_user, scopes=["admin-read", "customer-read"])
):
    invoice = await Invoice.get(id=invoice_id)
    if not current_user.is_admin:
        try:
            assert current_user.email == invoice.customer_email
        except AssertionError:
            raise HTTPException(403, "Unauthorized access")
    return await Invoice_Pydantic.from_queryset_single(Invoice.get(id=invoice_id))


@invoice_router.post("/{reservation_id}")
async def create_invoice(
    reservation_id: UUID,
    current_user: Customer = Security(get_current_active_user, scopes=["customer-write"])
):
    reservation = await Reservation.get(id=reservation_id).prefetch_related("customer")
    invoice = await Invoice.create(
        reservations_id=reservation.id,
        amount=await reservation.total_due(),
        customer_email=reservation.customer.email
    )
    return await Invoice_Pydantic.from_tortoise_orm(invoice)


@invoice_router.patch("/{invoice_id}", response_model=Invoice_Pydantic)
async def update_invoice_customer_email(
    invoice_id: UUID,
    invoice: InvoiceUpdate,
    current_user: Customer = Security(get_current_active_user, scopes=["customer-write"])
):
    invoice_obj = await Invoice.get(id=invoice_id)
    customer = await Customer.get(email=invoice_obj.customer_email)
    await authorize_obj_access(customer, current_user)
    invoice_obj.customer_email = invoice.email
    await invoice_obj.save()
    return await Invoice_Pydantic.from_queryset_single(Invoice.get(id=invoice_id))


@invoice_router.delete("/{invoice_id}", status_code=204)
async def delete_invoice(
    invoice_id: UUID,
    current_user: Admin = Security(get_current_active_user, scopes=["admin-write"])
):
    invoice = await Invoice.get(id=invoice_id)
    await invoice.delete()
    return {}


@checkout_router.post("/session/{invoice_id}")
async def make_invoice_payment(
    invoice_id: UUID,
    current_user: Customer = Security(get_current_active_user, scopes=["customer-write"])
):
    invoice = await Invoice.get(id=invoice_id)
    reservation = await Reservation.get(id=invoice.reservations_id).prefetch_related("room", "customer")
    try:
        desc = f"Reservation for {reservation.room.room_type} Room (Room #{reservation.room.room_number})"
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    "quantity": 1,
                    "price_data": {
                        "currency": "usd", 
                        "unit_amount": int(invoice.amount*100), 
                        "product_data": {
                            "name": "Room Reservation",
                            "description": desc
                        }
                    },
                },
                 {
                    "quantity": 1,
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": 5500,
                        "product_data": {
                            "name": "Room Service",
                            "description": "Additional Room Service Fee"
                        }
                    }
                }
            ],
            customer_email=invoice.customer_email,
            mode="payment",
            success_url=f"{settings.host_url}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.host_url}/checkout/cancelled",
            payment_method_types=["card", "paypal"],
            payment_intent_data={
                "description": desc,
                "metadata": {
                    "Reservation ID": str(reservation.id),
                    "Customer name": reservation.customer.full_name(),
                    "Customer email": reservation.customer.email,
                    "Room number": reservation.room.room_number,
                    "Room type": reservation.room.room_type,
                }
            },
            invoice_creation={
                "enabled": True,
                "invoice_data": {"description": desc}
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    invoice.transaction_id = checkout_session.id
    await invoice.save()
    return RedirectResponse(checkout_session.url, status_code=303)


@checkout_router.get("/success", response_model=dict[str, str])
async def payment_successful(
    session_id: Optional[str] = None, 
    current_user: Customer = Security(get_current_active_user, scopes=["customer-write"])
):
    invoice = await Invoice.get(transaction_id=session_id)
    invoice.status = PaidStatus.paid
    await invoice.save()
    return {"message": "Payment Successful"}


@checkout_router.get("/cancelled", response_model=dict[str, str])
async def payment_cancelled(
    current_user: Customer = Security(get_current_active_user, scopes=["customer-write"])
):
    return {"message": "Payment Cancelled"}
