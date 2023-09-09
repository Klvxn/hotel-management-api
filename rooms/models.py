import uuid

from tortoise import Tortoise, fields, models
from tortoise.contrib.pydantic import pydantic_model_creator

from users.models import Customer


class Room(models.Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    room_number = fields.IntField(index=True, unique=True)
    booked = fields.BooleanField(default=False)
    capacity = fields.CharField(max_length=500)
    price = fields.DecimalField(max_digits=5, decimal_places=3)

    reservations: fields.ReverseRelation["Reservation"]

    class Meta:
        ordering = ("room_number",)

    def __str__(self) -> str:
        return f"Room: {self.room_number}"

    @classmethod
    async def get_by_room_number(cls, room_number: int):
        return await Room.get(room_number=room_number)


class Reservation(models.Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    room: fields.ForeignKeyRelation[Room] = fields.ForeignKeyField(
        "models.Room", related_name="reservations", on_delete=fields.CASCADE
    )
    occupants = fields.IntField()
    customer: fields.ForeignKeyRelation[Customer] = fields.ForeignKeyField(
        "models.Customer", related_name="reservations", on_delete=fields.NO_ACTION
    )
    created_at = fields.DatetimeField(auto_now_add=True)
    check_in_date = fields.DatetimeField()
    check_out_date = fields.DatetimeField()

    class Meta:
        ordering = ("-created_at",)


Tortoise.init_models(["rooms.models", "users.models"], "models")
Room_Pydantic = pydantic_model_creator(Room)
RoomIn_Pydantic = pydantic_model_creator(
    Room, name="RoomIn", exclude=("id", "booked", "reservations")
)
Reservation_Pydantic = pydantic_model_creator(Reservation)
