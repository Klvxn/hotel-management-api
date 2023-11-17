import yagmail
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from ..config import settings
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
    with yagmail.SMTP(settings.email_user, settings.email_password) as yag:
        yag.send(
            to=customer_obj.email,
            subject=f"New Signee! {customer_obj.first_name} 🌟", 
            contents=f"""
            Welcome to the family! We are so excited to have you on board.
            Dear {customer_obj.first_name},

            At [Your Company Name], we believe in creating memorable experiences, and having you join us adds an exciting chapter to our journey. As you're here for our exceptional services, you're now a valued member of our family.

            Here's to new beginnings, shared moments, and the wonderful adventures ahead!

            If you have any questions or need assistance, feel free to reach out. We're here to make your experience extraordinary.

            Best regards,
            [Your Company Name] Team
            """
        )
        
    return await Customer_Pydantic.from_tortoise_orm(customer_obj)


@auth_router.post("/refresh", response_model=dict)
async def refresh_expired_token(current_user: BaseUser = Depends(get_current_active_user)):
    
    pass


@auth_router.post("/log-out")
async def log_out(current_user: BaseUser = Depends(get_current_active_user)):
    
    return {"message": "Logged out successfully"}


@auth_router.get("/password-reset")
async def password_reset_request(
    email: str, current_user: BaseUser = Depends(get_current_active_user)
):
    pass