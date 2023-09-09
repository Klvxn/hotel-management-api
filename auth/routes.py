from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from schemas import TokenResponse
from users.models import Customer_Pydantic, CustomerIn_Pydantic, Customer
from .utils import (
    ACCESS_TOKEN_EXPIRES,
    ADMIN_SCOPES,
    CUSTOMER_SCOPES,
    authenticate_user,
    create_access_token,
    hash_password,
    SUPERUSER_SCOPES,
)

auth_router = APIRouter(tags=["Auth"])


@auth_router.post("/login/t", response_model=TokenResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    scopes = form_data.scopes
    if not scopes:
        if not user.is_admin:
            scopes = list(CUSTOMER_SCOPES.keys())
        elif not user.is_superuser:
            scopes = list(ADMIN_SCOPES.keys())
        else:
            scopes = list(SUPERUSER_SCOPES.keys())
    access_token = create_access_token(
        data={"sub": user.email, "scopes": scopes},
        expires_delta=ACCESS_TOKEN_EXPIRES,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.post("/sign-up", response_model=Customer_Pydantic, status_code=201)
async def sign_up_new_customers(customer: CustomerIn_Pydantic):
    password = customer.dict().pop("password_hash")
    customer_obj = await Customer(**customer.dict(exclude=("password_hash",)))
    customer_obj.password_hash = hash_password(password)
    await customer_obj.save()
    return await Customer_Pydantic.from_tortoise_orm(customer_obj)
