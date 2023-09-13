from uuid import uuid4
from datetime import date

from tortoise import fields, models, Tortoise
from tortoise.contrib.pydantic import pydantic_model_creator

from ..rooms.models import Reservation


class BaseUser(models.Model):
    uid = fields.UUIDField(pk=True, default=uuid4)
    first_name = fields.CharField(max_length=50)
    last_name = fields.CharField(max_length=50)
    email = fields.CharField(max_length=100, unique=True, index=True)
    password_hash = fields.CharField(max_length=200, unique=True)
    joined_at = fields.DateField(default=date.today)

    class Meta:
        abstract = True
        ordering = ("-joined_at",)

    class PydanticMeta:
        computed = ("full_name",)

    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name()

    @classmethod
    async def get_by_email(cls, email: str):
        return await cls.get_or_none(email=email)


class Admin(BaseUser):
    is_superuser = fields.BooleanField(default=False)
    is_admin = fields.BooleanField(default=True)

    class PydanticMeta:
        computed = ("full_name",)
        exclude = ("password_hash",)


class Customer(BaseUser):
    is_admin = fields.BooleanField(default=False)
    reservations: fields.ReverseRelation[Reservation]

    class PydanticMeta:
        exclude = ("is_admin", "is_superuser", "password_hash")
        computed = ("full_name",)

    async def all_active_reservations(self):
        active = []
        reservations = await self.reservations.all()
        for i in reservations:
            if not i.customer_checked_out:
                active.append(i)
        return active


Tortoise.init_models(["app.rooms.models", "app.users.models"], "models")
Admin_Pydantic = pydantic_model_creator(Admin, name="Admin")
Customer_Pydantic = pydantic_model_creator(Customer, name="Customer")
