from uuid import uuid4
from datetime import date

from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator


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


Admin_Pydantic = pydantic_model_creator(Admin, name="Admin", exclude=("password_hash",))
AdminIn_Pydantic = pydantic_model_creator(
    Admin, name="AdminIn", exclude=("uid", "joined_at")
)
AdminUpdate = pydantic_model_creator(
    Admin, exclude=("password_hash", "id", "joined_at")
)


class Customer(BaseUser):
    is_admin = fields.BooleanField(default=False)
    reservations: fields.ReverseRelation

    class PydanticMeta:
        exclude = ("is_admin", "password_hash")


Customer_Pydantic = pydantic_model_creator(
    Customer,
    name="Customer",
)
CustomerIn_Pydantic = pydantic_model_creator(
    Customer, name="CustomerIn", exclude=("uid", "joined_at")
)
CustomerUpdate = pydantic_model_creator(Customer, exclude=("uid", "joined_at"))
