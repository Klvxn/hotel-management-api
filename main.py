from fastapi import APIRouter, FastAPI, Security
from fastapi.middleware.cors import CORSMiddleware
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise

from app.admin import app as admin_app
from app.auth.routes import auth_router
from app.auth.utils import get_current_active_admin
from app.checkout.routes import checkout_router
from app.config import settings
from app.guest_requests.routes import guest_request
from app.reservations.routes import admin_reservation_router, guest_reservation_router
from app.rooms.routes import admin_rooms_router, guest_rooms_router
from app.users.routes import admin_router, guest_router

api = FastAPI(
    title="Hotel Management API",
    summary="Welcome to the Hotel Management API - a powerful and efficient solution for managing hotel operations seamlessly.",
    description="""This API, crafted with FastAPI and Tortoise ORM, empowers hoteliers with a suite of features
    to streamline reservations, room management, and guest interactions. 
    From real-time booking updates to comprehensive room status tracking, our API simplifies the complexities of hotel administration,
    allowing you to focus on delivering exceptional guest experiences.
    Explore our endpoints to effortlessly integrate reservation systems, handle guest requests, and gain valuable insights into your hotel's performance. 
    Elevate your hotel management capabilities with the Hotel Management API - where efficiency meets excellence.""",
    version="1.0.0",
    docs_url="/api_docs",
)

router_v1 = APIRouter(prefix="/api/v1")
admin_routers_v1 = APIRouter(
    prefix="/api/v1/_restricted/admins",
    dependencies=[
        Security(
            get_current_active_admin,
            scopes=["admin-read", "admin-write", "superuser-rw"],
        )
    ],
)

# User and authentication routes
router_v1.include_router(auth_router)
admin_routers_v1.include_router(admin_router)
router_v1.include_router(guest_router, prefix="/usr")

# Room routers enable_captcha=Tru,
admin_routers_v1.include_router(admin_rooms_router, prefix="/rooms")
router_v1.include_router(guest_rooms_router, prefix="/rooms")

# Reservation routers
admin_routers_v1.include_router(admin_reservation_router, prefix="/reservations")
router_v1.include_router(guest_reservation_router, prefix="/reservations")

router_v1.include_router(checkout_router)

# Guest request routers
router_v1.include_router(guest_request, prefix="/requests")


api.include_router(router_v1)
api.include_router(admin_routers_v1)

api.mount("/admin", admin_app)
api.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)

TORTOISE_ORM = settings.TORTOISE_CONFIG
MODEL_PATHS = settings.MODEL_PATHS


async def init():
    Tortoise.init_models(MODEL_PATHS, "models")
    await Tortoise.init(config=TORTOISE_ORM, use_tz=True, timezone="WAT")


register_tortoise(api, config=TORTOISE_ORM, add_exception_handlers=True)

if __name__ == "__main__":
    import asyncio

    asyncio.run(init())
