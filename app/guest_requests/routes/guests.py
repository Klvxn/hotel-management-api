from fastapi import Depends, HTTPException
from fastapi.routing import APIRouter
from tortoise.transactions import in_transaction

from ..models import GuestRequest
from ..schema import GuestRequest_In, GuestRequest_Pydantic, GuestRequest_Pydantic_List
from ...auth.utils import get_current_active_user
from ...rooms.models import Room
from ...users.models import Guest


guest_request_router = APIRouter(tags=["Guest Request"])


@guest_request_router.get("/", response_model=GuestRequest_Pydantic_List)
async def get_request():
    return await GuestRequest_Pydantic.from_queryset(GuestRequest.all())
