from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str
    scopes: list[str]


class ReservationSchema(BaseModel):
    reservation_id: UUID = Field(default_factory=uuid4, serialization_alias="id")
    room_number: int
    customer_email: str | None = None
    occupants: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    check_in_date: datetime
    check_out_date: datetime


class ReservationUpdateSchema(BaseModel):
    room_number: int
    occupants: int
    check_in_date: datetime
    check_out_date: datetime
