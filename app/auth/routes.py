import yagmail
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from ..config import settings
from ..users.schema import UserIn, TokenResponse
from ..users.models import BaseUser, Admin
from .utils import (
    ADMIN_SCOPES,
    SUPERUSER_SCOPES,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_active_user,
)

auth_router = APIRouter(tags=["Auth"])


@auth_router.post("/login", response_model=TokenResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    print(user)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    scopes = form_data.scopes
    if not scopes:
        if not user.is_admin:
            scopes = ["guest-read-write"]
        elif isinstance(user, Admin) and not user.is_superuser:
            scopes = list(ADMIN_SCOPES.keys())
        else:
            scopes = list(SUPERUSER_SCOPES.keys())
    access_token = create_access_token(
        data={"sub": str(user.uid), "scopes": scopes},
    )
    refresh_token = create_refresh_token(data={"sub": str(user.uid), "scopes": scopes})
    return {"access_token": access_token, "refresh_token": refresh_token}


async def onboading_new_signee(guest: UserIn):
    with yagmail.SMTP(settings.email_user, settings.email_password) as yag:
        yag.send(
            to=guest.email,
            subject=f"New Signee! {guest.first_name} 🌟",
            contents=f"""
            Welcome to the family! We are so excited to have you on board.
            Dear {guest.first_name},

            At [Your Company Name], we believe in creating memorable experiences,
            and having you join us adds an exciting chapter to our journey. 
            As you're here for our exceptional services, you're now a valued member of our family.

            Here's to new beginnings, shared moments, and the wonderful adventures ahead!

            If you have any questions or need assistance, feel free to reach out. 
            We're here to make your experience extraordinary.

            Best regards,
            [Your Company Name] Team
            """,
        )


@auth_router.post("/refresh", response_model=dict)
async def refresh_expired_token(
    current_user: BaseUser = Depends(get_current_active_user),
):

    pass


@auth_router.post("/log-out")
async def log_out(current_user: BaseUser = Depends(get_current_active_user)):

    return {"message": "Logged out successfully"}


@auth_router.get("/password-reset")
async def password_reset_request(
    email: str, current_user: BaseUser = Depends(get_current_active_user)
):
    pass
