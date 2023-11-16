from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from ..schemas import Customer_Pydantic, UserIn, TokenResponse
from ..users.models import BaseUser, Customer
from .utils import (
    ADMIN_SCOPES,
    SUPERUSER_SCOPES,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_active_user,
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
            scopes = ["customer-read-write"]
        elif not user.is_superuser:
            scopes = list(ADMIN_SCOPES.keys())
        else:
            scopes = list(SUPERUSER_SCOPES.keys())
    access_token = create_access_token(
        data={"sub": str(user.uid), "scopes": scopes},
    )
    refresh_token = create_refresh_token(data={"sub": str(user.uid), "scopes": scopes})
    return {"access_token": access_token, "refresh_token": refresh_token}


@auth_router.post("/sign-up", response_model=Customer_Pydantic, status_code=201)
async def sign_up_new_customers(customer: UserIn):
    password = customer.password
    customer_obj = await Customer(**customer.model_dump(exclude={"password_hash"}))
    customer_obj.password_hash = hash_password(password.get_secret_value())
    await customer_obj.save()
    return await Customer_Pydantic.from_tortoise_orm(customer_obj)


@auth_router.post("/refresh", response_model=dict)
async def refresh_expired_token(current_user: BaseUser = Depends(get_current_active_user)):
    pass


@auth_router.post("/log-out")
async def log_out(current_user: BaseUser = Depends(get_current_active_user)):
    
    return {"message": "Logged out successfully"}
