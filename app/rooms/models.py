import uuid
from decimal import Decimal
from enum import Enum

from tortoise import fields, models


class Room(models.Model):
    class RoomType(str, Enum):
        STANDARD = "Standard"
        DELUXE = "Deluxe"
        SUITE = "Suite"

    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    room_type = fields.CharEnumField(RoomType, max_length=10, null=True)
    room_number = fields.IntField(index=True, unique=True)
    booked = fields.BooleanField(default=False)
    capacity = fields.CharField(max_length=500)
    price = fields.DecimalField(
        max_digits=5, decimal_places=3, description="price of room per night"
    )

    reservations: fields.ReverseRelation["Reservation"]
    reviews: fields.ReverseRelation["Review"]

    class Meta:
        ordering = ("room_number",)

    def __str__(self) -> str:
        return f"<Room: {self.room_number}>"

    @classmethod
    async def get_by_room_number(cls, room_number: int):
        return await Room.get(room_number=room_number)


class Reservation(models.Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    room: fields.ForeignKeyRelation[Room] = fields.ForeignKeyField(
        "models.Room", related_name="reservations", on_delete=fields.CASCADE
    )
    occupants = fields.IntField()
    customer = fields.ForeignKeyField(
        "models.Customer", related_name="reservations", on_delete=fields.NO_ACTION
    )
    created_at = fields.DatetimeField(auto_now_add=True)
    check_in_date = fields.DatetimeField()
    check_out_date = fields.DatetimeField()
    customer_checked_out = fields.BooleanField(default=False)

    class Meta:
        ordering = ("-created_at",)

    class PydanticMeta:
        computed = ("total_due",)

    def total_due(self) -> Decimal:
        room = self.room
        duration_of_stay = (self.check_out_date - self.check_in_date).total_seconds()
        return room.price * Decimal(duration_of_stay / (3600 * 24))


class Review(models.Model):
    id = fields.IntField(pk=True)
    room = fields.ForeignKeyField(
        "models.Room", related_name="reviews", on_delete=fields.CASCADE
    )
    customer = fields.ForeignKeyField(
        "models.Customer", related_name="reviews", on_delete=fields.NO_ACTION
    )
    created_at = fields.DatetimeField(auto_now_add=True)
    rating = fields.IntField(default=0)
    comment = fields.TextField(null=True)

    class Meta:
        ordering = ("-created_at",)
