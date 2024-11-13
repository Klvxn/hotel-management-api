from enum import Enum
from tortoise import fields, models


class RequestType(str, Enum):
    HOUSE_KEEPING = "house_keeping"
    MAINTENANCE = "maintenance"
    DINING = "dining"
    EXTRA_AMENITIES = "extra_amenities"


class RequestStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class RequestPriority(str, Enum):
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class GuestRequest(models.Model):

    id = fields.IntField(pk=True)
    request = fields.TextField()
    request_type = fields.CharEnumField(RequestType, max_length=20)
    request_status = fields.CharEnumField(RequestStatus)
    room = fields.ForeignKeyField(
        "models.Room", related_name="request", on_delete=fields.NO_ACTION
    )
    priority = fields.CharEnumField(RequestPriority, max_length=10, null=True)
    extra = fields.TextField(null=True)
    created = fields.DatetimeField(auto_now_add=True)
    updated = fields.DatetimeField(auto_now=True)
    guest = fields.ForeignKeyField(
        "models.Guest", related_name="requests", on_delete=fields.NO_ACTION
    )
    reservation = fields.ForeignKeyField(
        "models.Reservation", related_name="requests", null=True
    )

    class PydanticMeta:
        exclude = ("reservation",)
