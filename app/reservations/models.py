import uuid

from enum import Enum
from decimal import Decimal

from tortoise import fields, models


class Reservation(models.Model):
    class ReservationStatus(str, Enum):
        PENDING = "pending"
        CONFIRMED = "confirmed"
        CHECKED_IN = "checked_in"
        CHECKED_OUT = "checked_out"
        CANCELLED = "cancelled"

    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    rooms = fields.ManyToManyField("models.Room", through="models.RoomAvailability")
    occupants = fields.IntField()
    guest = fields.ForeignKeyField(
        "models.Guest", related_name="reservations", on_delete=fields.NO_ACTION
    )
    created_at = fields.DatetimeField(auto_now_add=True)
    check_in_date = fields.DatetimeField()
    check_out_date = fields.DatetimeField()
    guest_checked_out = fields.BooleanField(default=False)
    status = fields.CharEnumField(ReservationStatus, default=ReservationStatus.PENDING)

    class Meta:
        ordering = ("-created_at",)

    class PydanticMeta:
        exclude = ("availabilities",)

    def reservation_due(self) -> Decimal:
        room = self.rooms
        duration_of_stay = (self.check_out_date - self.check_in_date).total_seconds()
        return room.price * Decimal(duration_of_stay / (3600 * 24))
