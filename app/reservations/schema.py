from datetime import datetime

from pydantic import BaseModel, Field, model_validator, field_validator
from tortoise.contrib.pydantic import pydantic_model_creator, pydantic_queryset_creator

from .models import Reservation 


Reservation_Pydantic_List = pydantic_queryset_creator(Reservation)
ReservationBase_Pydantic = pydantic_model_creator(Reservation)
Reservation_Pydantic = pydantic_model_creator(Reservation)


class ReservationHistory(BaseModel):
    Reservation: ReservationBase_Pydantic
    reservations: Reservation_Pydantic_List

    
class ReservationIn(BaseModel):
    room_numbers: list[int] = Field(
        ..., max_length=5, min_length=1, description="List of room numbers to book"
    )
    occupants: int = Field(..., gt=0, le=5)
    check_in_date: datetime
    check_out_date: datetime

    @model_validator(mode="after")
    def validate_dates(self):
        if self.check_in_date >= self.check_out_date:
            raise ValueError("Check-out must be after check-in")
        if self.check_in_date.date() < datetime.now().date():
            raise ValueError("Check-in cannot be in the past")
        if (self.check_out_date - self.check_in_date).days > 30:
            raise ValueError("Maximum stay is 30 days")
        return self

    @field_validator("room_numbers")
    @classmethod
    def validate_unique_room_numbers(cls, room_numbers):
        if len(room_numbers) != len(set(room_numbers)):
            raise ValueError("Duplicate room numbers are not allowed.")
        return room_numbers
