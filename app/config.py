import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from pydantic import EmailStr
from pydantic_settings import BaseSettings


parent_dir = Path().resolve().parent
load_dotenv(parent_dir)


class Settings(BaseSettings):
    api_key: str = "my_key"
    superuser_email: EmailStr = "johndoe@example.com"
    stripe_secret_key: str = os.getenv("STRIPE_API_KEY", "my_stripe_key")
    host_url: str = "http://localhost:8081"
    email_user: str = os.getenv("EMAIL_USERNAME", "my_email")
    email_password: str = os.getenv("EMAIL_PASSWORD", "my_password")
    SECRET_KEY: str = "secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRES: timedelta = timedelta(hours=1)
    REFRESH_TOKEN_EXPIRES: timedelta = timedelta(days=14)
    tortoise_config: dict = {
        "connections": {
            "default": {
                "engine": "tortoise.backends.sqlite",
                "credentials": {"file_path": "db.sqlite3"},
            },
            "postgres": "postgres://postgres:postgres@127.0.0.1:5432/hotel_database",
        },
        "apps": {
            "models": {
                "models": [
                    "app.rooms.models",
                    "app.users.models",
                    "app.checkout.models",
                    "aerich.models",
                ],
                "default_connection": "postgres",
            },
        },
    }


settings = Settings(_env_file=f"{parent_dir}/.env")
