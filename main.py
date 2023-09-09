from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from auth.routes import auth_router
from rooms.routes import room_router, reservation_router
from users.routes.customers import customer_router
from users.routes.admins import admin_router


api = FastAPI(
    title="Hotel Management API",
    description="API for a hotel management system",
    version="0.1",
)

api.include_router(admin_router)
api.include_router(auth_router)
api.include_router(customer_router)
api.include_router(room_router)
api.include_router(reservation_router)

register_tortoise(
    api,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["rooms.models", "users.models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)
