from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise

from app.auth.routes import auth_router
from app.rooms.routes import room_router, reservation_router, review_router
from app.users.routes.admins import admin_router
from app.users.routes.customers import customer_router


api = FastAPI(
    title="Hotel Management API",
    description="API for a hotel management system",
    version="1.0",
)

api.include_router(admin_router)
api.include_router(auth_router)
api.include_router(customer_router)
api.include_router(room_router)
api.include_router(reservation_router)
api.include_router(review_router)
api.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)


TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.sqlite",
            "credentials": {"file_path": "db.sqlite3"},
        },
    },    
    "apps": {
        "models": {
            "models": ["app.rooms.models", "app.users.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}


async def init():
    await Tortoise.init(config=TORTOISE_ORM, use_tz=True, timezone="WAT")
    

register_tortoise(
    api,
    config=TORTOISE_ORM,
    add_exception_handlers=True
)
