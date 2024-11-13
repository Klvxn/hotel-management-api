from enum import Enum
from uuid import uuid4
from tortoise import fields, models


class PaidStatus(str, Enum):
    paid = "paid"
    unpaid = "unpaid"


class Invoice(models.Model):
    id = fields.UUIDField(pk=True, default=uuid4)
    reservation = fields.OneToOneField("models.Reservation", related_name="invoice")
    created_at = fields.DatetimeField(auto_now_add=True)
    status = fields.CharEnumField(PaidStatus, default="unpaid")
    transaction_id = fields.CharField(max_length=100, null=True)
    guest_email = fields.CharField(max_length=100)
    amount = fields.DecimalField(max_digits=6, decimal_places=3, null=True)

    def __str__(self) -> str:
        return f"Invoice for reservation: {self.reservation.id} - {self.guest_email}"
