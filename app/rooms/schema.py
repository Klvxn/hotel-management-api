from typing import Optional

from pydantic import BaseModel, model_validator, field_validator
from tortoise.contrib.pydantic import pydantic_model_creator, pydantic_queryset_creator

from .models import Room, Review
from ..schemas import ReservationBase_Pydantic


Room_Pydantic_List = pydantic_queryset_creator(Room)
RoomBase_Pydantic = pydantic_model_creator(Room)
RoomIn_Pydantic = pydantic_model_creator(
    Room, exclude=("id", "reservations", "reviews")
)

class RoomHistory(BaseModel):
    room: RoomBase_Pydantic
    reservations: list[ReservationBase_Pydantic]

    class Config:
        from_attributes = True


Room_Reviews_Pydantic = pydantic_model_creator(Room, exclude=("reservations",))
Review_Pydantic = pydantic_model_creator(Review)


class ReviewIn(BaseModel):
    rating: Optional[int] = None
    comment: Optional[str] = None

    @field_validator("rating")
    @classmethod
    def validate_rating_range(cls, value: int):
        try:
            assert 0 <= value <= 10
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
