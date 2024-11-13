import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from pydantic import EmailStr
from pydantic_settings import BaseSettings


parent_dir = Path().resolve().parent
load_dotenv()


class Settings(BaseSettings):
    api_key: str = "my_key"
    superuser_email: EmailStr = "johndoe@example.com"
    stripe_secret_key: str = os.getenv("STRIPE_API_KEY", "my_stripe_key")
    host_url: str = "http://localhost:8081"
    email_user: str = os.getenv("EMAIL_USER", "my_email")
    email_password: str = os.getenv("EMAIL_PASSWORD", "my_password")
    SECRET_KEY: str = "secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRES: timedelta = timedelta(hours=1)
    REFRESH_TOKEN_EXPIRES: timedelta = timedelta(days=14)
    MODEL_PATHS: list[str] = [
        "app.rooms.models",
        "app.reservations.models",
        "app.users.models",
        "app.guest_requests.models",
        "app.checkout.models",
        "aerich.models",
    ]
    tortoise_config: dict[str, dict] = {
        "connections": {
            "default": {
                "engine": "tortoise.backends.sqlite",
                "credentials": {"file_path": "dab.sqlite3"},
            },
            "postgres": "postgres://postgres:postgres@127.0.0.1:5432/hotel_database",
        },
        "apps": {
            "models": {
                "models": MODEL_PATHS,
                "default_connection": "default",
            },
        },
    }


settings = Settings(_env_file=f"{parent_dir}/.env")
