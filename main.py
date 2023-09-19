from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

register_tortoise(
    api,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["app.rooms.models", "app.users.models"]},
    generate_schemas=False,
    add_exception_handlers=True,
)
