"""
This module contains utility functions for authentication and authorization in the Hotel Management API.
It includes functions for verifying and hashing passwords, creating access and refresh tokens, and authenticating users.
It also includes functions for getting the current user and authorizing object and user access.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.rooms.models import Reservation, Review

from ..schemas import TokenData
from ..config import settings
from ..users.models import Admin, Customer, BaseUser
from uuid import UUID


logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ADMIN_SCOPES = {
    "admin-read": "admin read only role",
    "admin-write": "admin write only role",
}
SUPERUSER_SCOPES = {
    "superuser-read": "super user read access",
    "superuser-write": "super user write access",
}

scopes = {**ADMIN_SCOPES, **SUPERUSER_SCOPES}
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login/t", scopes=scopes)


def verify_password(plain_password: str, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(plain_password):
    return pwd_context.hash(plain_password)


def create_token(data: dict, token_type: str, expires: timedelta):
    to_encode = data.copy()
    to_encode.update({"token_type": token_type, "exp": datetime.utcnow() + expires})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_access_token(data: dict):
    return create_token(
        data, token_type="access", expires=settings.ACCESS_TOKEN_EXPIRES
    )


def create_refresh_token(data: dict):
    return create_token(
        data, token_type="refresh", expires=settings.REFRESH_TOKEN_EXPIRES
    )


# TODO: Revoke Access token


async def verify_user(user_uid: Optional[UUID] = None, email: Optional[str] = None):
    if user_uid:
        admin = await Admin.get_or_none(uid=user_uid)
        customer = await Customer.get_or_none(uid=user_uid)
        return admin or customer
    if email:
        admin = await Admin.get_by_email(email)
        customer = await Customer.get_by_email(email)
        return admin or customer


async def authenticate_user(email: str, password: str):
    user = await verify_user(email=email)
    if user and verify_password(password, user.password_hash):
        return user
    return False


async def get_current_user(
    security_scope: SecurityScopes = SecurityScopes(), 
    token: str = Depends(oauth2_scheme)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    headers = (
        {"WWW-Authenticate": f"Bearer {security_scope.scope_str}"}
        if security_scope.scopes
        else {"WWW-Authenticate": "Bearer"}
    )
    scope_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not enough permissions",
        headers=headers,
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: UUID = payload["sub"]
        if user_id is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        data = TokenData(user_id=user_id, scopes=token_scopes)
    except JWTError as e:
        credentials_exception.detail = str(e)
        logger.error(e)
        raise credentials_exception
    user = await verify_user(user_uid=data.user_id)
    if not user:
        raise credentials_exception
    logger.info(f"User {user} authenticated successfully, payload: {payload}")
    if not security_scope.scopes:
        return user
    for scope in security_scope.scopes:
        if scope in data.scopes:
            return user
    raise scope_exception


async def get_current_active_user(current_user: Customer = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def authorize_obj_access(
    obj: BaseUser | Reservation | Review,
    current_user: BaseUser,
    allow_superuser: bool = True,
):
    if allow_superuser and current_user.is_superuser:
        return True
    if isinstance(obj, BaseUser):
        return await authorize_user_access(obj, current_user)
    try:
        assert obj.customer == current_user
        return True
    except AssertionError:
        raise HTTPException(403, "Unauthorized access")
    
    
async def authorize_user_access(obj: BaseUser, current_user: BaseUser):
    try:
        assert obj == current_user
        return True
    except AssertionError:
        raise HTTPException(403, "Unauthorized access")
    