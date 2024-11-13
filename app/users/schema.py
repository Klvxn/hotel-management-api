from datetime import date
from uuid import UUID

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    SecretStr,
)
from tortoise.contrib.pydantic.creator import pydantic_model_creator

from .models import Admin, Guest
from ..reservations.schema import Reservation_Pydantic_List


Admin_Pydantic = pydantic_model_creator(Admin)
Guest_Pydantic = pydantic_model_creator(Guest)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str


class TokenData(BaseModel):
    user_id: UUID
    scopes: list[str]


class UserIn(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: SecretStr = Field(serialization_alias="password_hash")


class GuestBase(BaseModel):
    uid: UUID
    first_name: str
    last_name: str
    email: EmailStr
    joined_at: date
    is_active: bool
    full_name: str


class GuestReservations(GuestBase):
    reservations: Reservation_Pydantic_List


class UserUpdate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr


class RoomGuests(BaseModel):
    id: UUID
    room_number: int
    guests: list[GuestBase]
