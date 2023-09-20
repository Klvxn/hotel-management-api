import os
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import jwt, JWTError
from passlib.context import CryptContext

from ..schemas import TokenData
from ..users.models import Admin, Customer, BaseUser


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ADMIN_SCOPES = {
    "admin-read": "admin read only role",
    "admin-write": "admin write only role",
}
CUSTOMER_SCOPES = {
    "customer-read": "customer read only role",
    "customer-write": "customer write only role",
}
SUPERUSER_SCOPES = {
    "superuser-read": "super user read access",
    "superuser-write": "super user write access",
    **ADMIN_SCOPES,
    **CUSTOMER_SCOPES,
}

scopes = {**ADMIN_SCOPES, **CUSTOMER_SCOPES, **SUPERUSER_SCOPES}
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login/t", scopes=scopes)
SECRET_KEY = "secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRES = timedelta(hours=1)


def verify_password(plain_password: str, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(plain_password):
    return pwd_context.hash(plain_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = (
        datetime.utcnow() + expires_delta
        if expires_delta
        else datetime.utcnow() + ACCESS_TOKEN_EXPIRES
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# TODO: Refresh Access token


async def verify_user(email: str):
    admin = await Admin.get_or_none(email=email)
    customer = await Customer.get_or_none(email=email)
    if admin and not customer:
        return admin
    elif customer and not admin:
        return customer
    else:
        return


async def authenticate_user(email: str, password: str):
    user = await verify_user(email)
    if user and verify_password(password, user.password_hash):
        return user
    return False


async def get_current_user(
    security_scope: SecurityScopes, token: str = Depends(oauth2_scheme)
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
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        data = TokenData(email=username, scopes=token_scopes)
    except JWTError as e:
        credentials_exception.detail = e.args
        raise credentials_exception
    user = await verify_user(data.email)
    if not user:
        raise credentials_exception
    for i in security_scope.scopes:
        if i in data.scopes:
            return user
    raise scope_exception


async def get_current_active_user(current_user: Customer = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def authorize_customer_access(
    customer_uid: UUID,
    current_user: BaseUser,
    allow_admin: bool = True,
    allow_only_superuser: bool = True,
):
    if isinstance(current_user, Admin):
        if allow_admin and current_user.is_admin:
            return True
        if allow_only_superuser and current_user.is_superuser:
            return True
        raise HTTPException(403, "Unauthorized access")
    customer_obj = await Customer.get(uid=customer_uid)
    try:
        if isinstance(customer_obj, Customer):
            assert customer_obj == current_user
            return True
    except AssertionError:
        raise HTTPException(403, "Unauthorized access")


async def authorize_admin_access(
    admin_uid: UUID,
    current_user: Admin,
    allow_only_superuser: bool = True,
):
    admin_obj = await Admin.get(uid=admin_uid)
    if allow_only_superuser and current_user.is_superuser:
        return True
    try:
        assert admin_obj == current_user
        return True
    except AssertionError:
        raise HTTPException(403, "Unauthorized access")
