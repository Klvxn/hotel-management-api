from uuid import uuid4
from datetime import date

from tortoise import fields, models

from ..reservations.models import Reservation


class BaseUser(models.Model):
    uid = fields.UUIDField(pk=True, default=uuid4)
    first_name = fields.CharField(max_length=50)
    last_name = fields.CharField(max_length=50)
    email = fields.CharField(max_length=100, unique=True, index=True)
    password_hash = fields.CharField(max_length=200, unique=True)
    joined_at = fields.DateField(default=date.today)
    is_active = fields.BooleanField(default=True)
    is_admin = fields.BooleanField(default=False, editable=False)

    class Meta:
        abstract = True
        ordering = ("-joined_at",)
        
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"<{self.__class__.__name__}: {self.full_name()}>"

    @classmethod
    def get_by_email(cls, email: str):
        return cls.get_or_none(email=email)


class Admin(BaseUser):
    is_superuser = fields.BooleanField(default=False)

    class PydanticMeta:
        exclude = ("password_hash",)
        computed = ("full_name",)


class Guest(BaseUser):
    reservations: fields.ReverseRelation[Reservation]

    class PydanticMeta:
        exclude = ("password_hash", "reviews")
        computed = ("full_name",)

