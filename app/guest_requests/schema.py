from typing import Optional
from pydantic import BaseModel
from tortoise.contrib.pydantic import pydantic_model_creator, pydantic_queryset_creator

from .models import GuestRequest, RequestPriority, RequestStatus, RequestType
from ..users.models import Guest


GuestRequest_Pydantic = pydantic_model_creator(GuestRequest)
GuestRequest_Pydantic_List = pydantic_queryset_creator(GuestRequest)


class GuestRequest_In(BaseModel):
    room_number: int
    guest: Guest
    request: str
    req_type: RequestType
    status: RequestStatus
    priority: RequestPriority
    extra: Optional[str] = None
