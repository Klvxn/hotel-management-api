from datetime import datetime
from typing import Optional


from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    SecretStr,
    model_validator,
    field_validator,
)


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


class ReviewUpdate(BaseModel):
    rating: Optional[int]
    comment: Optional[str]
