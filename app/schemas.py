from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str
    scopes: list[str]


class ReservationIn(BaseModel):
    reservation_id: UUID = Field(default_factory=uuid4, serialization_alias="id")
    room_number: int
    customer_email: Optional[str] = None
    occupants: int
    check_in_date: datetime
    check_out_date: datetime


class ReservationUpdate(BaseModel):
    room_number: int
    occupants: int
    check_in_date: datetime
    check_out_date: datetime


class ReviewIn(BaseModel):
    rating: Optional[int] = None
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, exclude=True)

    @model_validator(mode="after")
    def check_mutually_exclusive(self):
        if not self.rating and not self.comment:
            raise ValueError(
                "Rating and comment are mutually exclusive. Only one can be omitted."
            )
        return self


class ReviewUpdate(BaseModel):
    rating: int
    comment: str
