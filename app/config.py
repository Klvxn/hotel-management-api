from datetime import timedelta

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_key: str = "my_key"
    stripe_secret_key: str =  "my_stripe_key"
    host_url: str = "http://localhost:8081"
    SECRET_KEY: str = "secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRES: timedelta = timedelta(hours=1)

    class Config:
        env_file = ".env"
        

settings = Settings()
