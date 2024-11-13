import uuid
from enum import Enum
from datetime import date

from tortoise import fields, models

from ..reservations.models import Reservation


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

    reservations: fields.ManyToManyRelation[Reservation]
    reviews: fields.ReverseRelation["Review"]

    class Meta:
        ordering = ("room_number",)

    class PydanticMeta:
        exclude = ("availabilities",)

    def __str__(self) -> str:
        return f"<Room: {self.room_number}>"

    @classmethod
    def get_by_room_number(cls, room_number: int):
        return cls.get(room_number=room_number)


class RoomAvailability(models.Model):
    id = fields.IntField(pk=True)
    room = fields.ForeignKeyField(
        "models.Room", related_name="availabilities", on_delete=fields.CASCADE
    )
    reservation = fields.ForeignKeyField(
        "models.Reservation", related_name="availabilities", on_delete=fields.CASCADE
    )
    booked = fields.BooleanField(default=False)
    start_date = fields.DateField()
    end_date = fields.DateField()

    class Meta:
        unique_together = ("room", "start_date", "end_date")

    @classmethod
    def check_room_is_available(cls, room: Room, start: date, end: date):
        return cls.filter(room=room, start_date__lt=end, end_date__gt=start).exists()

    @classmethod
    async def update_booked_status(
        cls, room: Room, start: date, end: date, booked: bool
    ):
        availabilities = await cls.filter(room=room, start_date=start, end_date=end)
        for availability in availabilities:
            availability.booked = booked
            await availability.save()


class Review(models.Model):
    id = fields.IntField(pk=True)
    room = fields.ForeignKeyField(
        "models.Room", related_name="reviews", on_delete=fields.CASCADE
    )
    guest = fields.ForeignKeyField(
        "models.Guest", related_name="reviews", on_delete=fields.NO_ACTION
    )
    created_at = fields.DatetimeField(auto_now_add=True)
    rating = fields.IntField(default=0)
    comment = fields.TextField(null=True)

    class Meta:
        ordering = ("-created_at",)

    class PydanticMeta:
        exclude = (
            "guest",
        )  # Use the `guest_id` field instead of it's objects (and relations)
