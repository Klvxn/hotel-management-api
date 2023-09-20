from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    SecretStr,
    model_validator,
    field_validator,
)
from tortoise import Tortoise
from tortoise.contrib.pydantic import pydantic_model_creator

from .rooms.models import Reservation, Review, Room
from .users.models import Admin, Customer


Tortoise.init_models(["app.rooms.models", "app.users.models"], "models")

Room_Pydantic = pydantic_model_creator(Room)
RoomIn_Pydantic = pydantic_model_creator(
    Room, name="RoomIn", exclude=("id", "reservations", "reviews")
)
Reservation_Pydantic = pydantic_model_creator(Reservation)
Review_Pydantic = pydantic_model_creator(Review, name="Review")
Admin_Pydantic = pydantic_model_creator(Admin, name="Admin")
Customer_Pydantic = pydantic_model_creator(Customer, name="Customer")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: EmailStr
    scopes: list[str]


class UserIn(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: SecretStr = Field(serialization_alias="password_hash")


class UserUpdate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr


class ReservationIn(BaseModel):
    room_number: int
    occupants: int
    check_in_date: datetime
    check_out_date: datetime


class ReservationUpdate(BaseModel):
    room_number: int
    occupants: int
    check_in_date: datetime
    check_out_date: datetime


class ReservationHistory(BaseModel):
    id: UUID
    customer_id: UUID
    room_id: UUID
    customer_checked_out: bool
    check_in_date: datetime
    check_out_date: datetime
    occupants: int
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewIn(BaseModel):
    rating: Optional[int] = None
    comment: Optional[str] = None

    @field_validator("rating")
    @classmethod
    def validate_rating_range(cls, value: int):
        try:
            assert 0 >= value <= 10
        except AssertionError:
            raise ValueError("Rating should be betweeen range 0 and 10")
        return value

    @model_validator(mode="after")
    def check_mutually_exclusive(self):
        if not self.rating and not self.comment:
            raise ValueError(
                "Rating and comment are mutually exclusive. Only one can be omitted."
            )
        return self


class RoomGuests(BaseModel):
    id: UUID
    room_number: int
    customers: list[UserUpdate]
