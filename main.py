import uuid
from datetime import date

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise

from app.auth.routes import auth_router
from app.auth.utils import hash_password
from app.checkout.routes import checkout_router
from app.config import settings
from app.guest_requests.routes import guest_request
from app.rooms.routes import admin_rooms, guest_rooms
from app.reservations.routes import admin_reservation, guest_reservation
from app.users.routes import admin_router, guest_router


api = FastAPI(
    title="Hotel Management API",
    summary="Welcome to the Hotel Management API - a powerful and efficient solution for managing hotel operations seamlessly.",
    description="""This API, crafted with FastAPI and Tortoise ORM, empowers hoteliers with a suite of features to streamline reservations, room management, and guest interactions. From real-time booking updates to comprehensive room status tracking, our API simplifies the complexities of hotel administration, allowing you to focus on delivering exceptional guest experiences. Explore our endpoints to effortlessly integrate reservation systems, handle guest requests, and gain valuable insights into your hotel's performance. Elevate your hotel management capabilities with the Hotel Management API - where efficiency meets excellence.""",
    version="1.0.0",
    docs_url="/api_docs",
)

router_v1 = APIRouter(prefix="/api/v1")

# User and authentication routes
router_v1.include_router(auth_router)
router_v1.include_router(admin_router, prefix="/_restricted/admins")
router_v1.include_router(guest_router, prefix="/usr")

# Room routers
router_v1.include_router(admin_rooms, prefix="/_restricted/admins/rooms")
router_v1.include_router(guest_rooms, prefix="/rooms")

# Reservation routers
router_v1.include_router(admin_reservation, prefix="/_restricted/admins/reservations")
router_v1.include_router(guest_reservation, prefix="/reservations")

router_v1.include_router(checkout_router)


# Guest request routers
router_v1.include_router(guest_request, prefix="/requests")

api.include_router(router_v1)
api.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)

TORTOISE_ORM = settings.tortoise_config


async def init():
    await Tortoise.init(config=TORTOISE_ORM, use_tz=True, timezone="WAT")
    Tortoise.init_models(settings.MODEL_PATHS, "models")

    async def seed_data():
        from app.rooms.models import Room
        from app.users.models import (
            Admin,
            Guest,
        )  # Adjust this import according to your project structure

        # Sample data for Room table
        rooms = [
            {
                "id": uuid.uuid4(),
                "room_type": Room.RoomType.STANDARD,
                "room_number": 101,
                "booked": False,
                "capacity": "2 guests",
                "price": 75.500,
            },
            {
                "id": uuid.uuid4(),
                "room_type": Room.RoomType.DELUXE,
                "room_number": 102,
                "booked": False,
                "capacity": "4 guests",
                "price": 150.750,
            },
            {
                "id": uuid.uuid4(),
                "room_type": Room.RoomType.SUITE,
                "room_number": 103,
                "booked": False,
                "capacity": "6 guests",
                "price": 300.000,
            },
        ]
        for room in rooms:
            await Room.create(**room)

        # Sample data for Admin table
        admin_data = {
            "uid": uuid.uuid4(),
            "first_name": "Admin",
            "last_name": "User",
            "email": "admin@example.com",
            "password_hash": hash_password(
                "hashed_password_here"
            ),  # Replace with an actual hash
            "joined_at": date.today(),
            "is_active": True,
            "is_admin": True,
            "is_superuser": True,
        }
        await Admin.create(**admin_data)

        # Sample data for Guest table
        guest_data = {
            "uid": uuid.uuid4(),
            "first_name": "Guest",
            "last_name": "User",
            "email": "guest@example.com",
            "joined_at": date.today(),
            "password_hash": hash_password(
                "hashed_password_here"
            ),  # Replace with an actual hash(),
            "is_active": True,
            "is_admin": False,
        }
        await Guest.create(**guest_data)

    await seed_data()


register_tortoise(api, config=TORTOISE_ORM, add_exception_handlers=True)

if __name__ == "__main__":
    import asyncio

    asyncio.run(init())
