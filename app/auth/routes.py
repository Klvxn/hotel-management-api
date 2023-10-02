from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from ..config import settings
from ..schemas import Customer_Pydantic, UserIn, TokenResponse
from ..users.models import Customer
from .utils import (
    ADMIN_SCOPES,
    SUPERUSER_SCOPES,
    authenticate_user,
    create_access_token,
    hash_password,
)


auth_router = APIRouter(tags=["Auth"])


@auth_router.post("/login/t", response_model=TokenResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    scopes = form_data.scopes
    if not scopes:
        if not user.is_admin:
            scopes = None
        elif not user.is_superuser:
            scopes = list(ADMIN_SCOPES.keys())
        else:
            scopes = list(SUPERUSER_SCOPES.keys())
    access_token = create_access_token(
        data={"sub": user.email, "scopes": scopes},
        expires_delta=settings.ACCESS_TOKEN_EXPIRES,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.post("/sign-up", response_model=Customer_Pydantic, status_code=201)
async def sign_up_new_customers(customer: UserIn):
    password = customer.password
    customer_obj = await Customer(**customer.model_dump(exclude={"password_hash"}))
    customer_obj.password_hash = hash_password(password.get_secret_value())
    await customer_obj.save()
    return await Customer_Pydantic.from_tortoise_orm(customer_obj)
