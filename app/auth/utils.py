"""
This module contains utility functions for authentication and authorization in the Hotel Management API.
It includes functions for verifying and hashing passwords, creating access and refresh tokens, and authenticating users.
It also includes functions for getting the current user and authorizing object and user access.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Union
from uuid import UUID

from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import jwt, JWTError
from passlib.context import CryptContext

from ..config import settings
from ..rooms.models import Review
from ..reservations.models import Reservation
from ..users.schema import TokenData
from ..users.models import Admin, Guest, BaseUser


logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ADMIN_SCOPES = {
    "admin-read": "admin read only role",
    "admin-write": "admin write only role",
}
SUPERUSER_SCOPES = {"superuser-rw": "superuser read, write access"}

scopes = {**ADMIN_SCOPES, **SUPERUSER_SCOPES}
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login", scopes=scopes)


def verify_password(plain_password: str, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(plain_password):
    return pwd_context.hash(plain_password)


def encode_token(data: dict, token_type: str, expires: timedelta):
    to_encode = data.copy()
    to_encode.update({"token_type": token_type, "exp": datetime.now() + expires})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_auth_token(data: dict, token_type: str):
    match token_type:
        case "access":
            return encode_token(data, token_type=token_type, expires=settings.ACCESS_TOKEN_EXPIRES)
        case "refresh":
            return encode_token(data, token_type=token_type, expires=settings.REFRESH_TOKEN_EXPIRES)
        case _:
            return


# TODO: Revoke Access token


async def verify_user(user_uid: Optional[UUID] = None, email: Optional[str] = None):
    if user_uid:
        admin = await Admin.get_or_none(uid=user_uid)
        guest = await Guest.get_or_none(uid=user_uid)
        return admin or guest
    if email:
        admin = await Admin.get_by_email(email)
        guest = await Guest.get_by_email(email)
        return admin or guest


async def authenticate_user(email: str, password: str):
    user = await verify_user(email=email)
    if user and verify_password(password, user.password_hash):
        return user
    return False


async def get_current_user(
    security_scope: SecurityScopes = SecurityScopes(), token: str = Depends(oauth2_scheme)
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
    logger.info(f"User {user} authenticated successfully.")
    if not security_scope.scopes:
        return user
    for scope in security_scope.scopes:
        if scope in data.scopes:
            return user
    raise scope_exception


async def get_current_active_user(current_user: Guest = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_active_admin(current_user: Admin = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def authorize_obj_access(
    obj: Union[BaseUser, Reservation, Review],
    current_user: BaseUser,
    allow_superuser: bool = True,
):
    if allow_superuser and current_user.is_superuser:
        return True
    if isinstance(obj, BaseUser):
        return await authorize_user_access(obj, current_user)
    try:
        assert obj.guest == current_user
        return True
    except AssertionError:
        raise HTTPException(403, "Unauthorized access")


async def authorize_user_access(obj: BaseUser, current_user: BaseUser):
    try:
        assert obj == current_user
        return True
    except AssertionError:
        raise HTTPException(403, "Unauthorized access")
