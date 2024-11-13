from typing import Optional
from uuid import UUID

import stripe
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.responses import RedirectResponse

from ..users.models import Admin, BaseUser, Guest
from .models import Invoice, PaidStatus
from ..auth.utils import authorize_obj_access, get_current_active_user
from ..config import settings
from ..reservations.models import Reservation
from ..schemas import Invoice_Pydantic, InvoiceUpdate


invoice_router = APIRouter(prefix="/invoices", tags=["Invoices"])
checkout_router = APIRouter(prefix="/checkout", tags=["Checkout"])

stripe.api_key = settings.stripe_secret_key


@invoice_router.get("/", response_model=list[Invoice_Pydantic])
async def get_invoices(
    status: Optional[PaidStatus] = None,
    guest_email: Optional[str] = None,
    current_user: Admin = Security(get_current_active_user, scopes=["admin-read"])
):
    query = Invoice.all()
    if status:
        query = query.filter(status=status)
    if guest_email:
        query = query.filter(guest_email=guest_email)
    return await Invoice_Pydantic.from_queryset(query)


@invoice_router.get("/{invoice_id}", response_model=Invoice_Pydantic)
async def get_invoice(
    invoice_id: UUID, 
    current_user: BaseUser = Depends(get_current_active_user)
):
    invoice = await Invoice.get(id=invoice_id)
    if not current_user.is_admin:
        try:
            assert current_user.email == invoice.guest_email
        except AssertionError:
            raise HTTPException(403, "Unauthorized access")
    return await Invoice_Pydantic.from_queryset_single(Invoice.get(id=invoice_id))


@invoice_router.post("/{reservation_id}")
async def create_invoice(
    reservation_id: UUID,
    current_user: Guest = Depends(get_current_active_user)
):
    reservation = await Reservation.get(id=reservation_id).prefetch_related("guest")
    invoice = await Invoice.create(
        reservation_id=reservation.id,
        amount=reservation.reservation_due(),
        guest_email=reservation.guest.email
    )
    return await Invoice_Pydantic.from_tortoise_orm(invoice)


@invoice_router.patch("/{invoice_id}", response_model=Invoice_Pydantic)
async def update_invoice_guest_email(
    invoice_id: UUID,
    invoice: InvoiceUpdate,
    current_user: Guest = Depends(get_current_active_user)
):
    invoice_obj = await Invoice.get(id=invoice_id)
    guest = await Guest.get(email=invoice_obj.guest_email)
    await authorize_obj_access(guest, current_user)
    invoice_obj.guest_email = invoice.email
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
async def create_checkout_session(
    invoice_id: UUID,
    current_user: Guest = Depends(get_current_active_user)
):
    invoice = await Invoice.get(id=invoice_id)
    reservation = await Reservation.get(id=invoice.reservation_id).prefetch_related("room", "guest")
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
            guest_email=invoice.guest_email,
            mode="payment",
            success_url=f"{settings.host_url}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.host_url}/checkout/cancelled",
            payment_method_types=["card", "paypal"],
            payment_intent_data={
                "description": desc,
                "metadata": {
                    "Reservation ID": str(reservation.id),
                    "guest name": reservation.guest.full_name(),
                    "guest email": reservation.guest.email,
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
    current_user: Guest = Depends(get_current_active_user)
):
    invoice = await Invoice.get(transaction_id=session_id)
    invoice.status = PaidStatus.paid
    await invoice.save()
    return {"message": "Payment Successful"}


@checkout_router.get("/cancelled", response_model=dict[str, str])
async def payment_cancelled(current_user: Guest = Depends(get_current_active_user)):
    return {"message": "Payment Cancelled"}
