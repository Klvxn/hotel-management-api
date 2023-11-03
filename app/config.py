from datetime import timedelta

from pydantic import EmailStr
from pydantic_settings import BaseSettings



class Settings(BaseSettings):
    api_key: str = "my_key"
    superuser_email: EmailStr = "johndoe@example.com"
    stripe_secret_key: str = "my_stripe_key"
    host_url: str = "http://localhost:8081"
    SECRET_KEY: str = "secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRES: timedelta = timedelta(hours=1)
    tortoise_config: dict[str, dict] = {
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

    class Config:
        env_file = ".env"


settings = Settings()
