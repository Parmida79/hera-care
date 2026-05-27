from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional, Any, Callable
from functools import wraps

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Member
from app.utils import get_current_user_from_token


# ---------- Auth config ----------
SECRET_KEY: str = os.getenv('SECRET_KEY')
ALGORITHM: str = os.getenv('JWT_ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Header-based auth (matches "Authorization: Bearer <token>")
auth_header = APIKeyHeader(name="Authorization", auto_error=False)

Role = Literal['admin', 'patient', 'super-admin']


# ---------- Password helpers ----------
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ---------- JWT helpers ----------
def create_access_token(
    subject: str,
    role: str,
    type_: str = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": subject,  # username
        "role": role,
        "type": type_,
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def _get_token_from_header(header_value: Optional[str]) -> str:
    """
    Supports both:
      Authorization: Bearer <token>
      Authorization: <token>
    """
    if not header_value:
        return ""
    header_value = header_value.strip()
    if header_value.lower().startswith("bearer "):
        return header_value.split(" ", 1)[1].strip()
    return header_value


# ---------- User helpers ----------
def get_user_by_username(session: Session, username: str) -> Optional[Member]:
    """Member is polymorphic; querying Member loads the correct subclass."""
    return session.execute(
        select(Member).where(Member.username == username)
    ).scalar_one_or_none()


def authenticate_user_db(
    session: Session, username: str, password: str
) -> Optional[Member]:
    user = get_user_by_username(session, username)
    if not user:
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# ---------- FastAPI dependency ----------
def get_current_user(
    authorization: Optional[str] = Depends(auth_header),
    session: Session = Depends(get_db),
) -> Member:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )

    token = _get_token_from_header(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token",
        )

    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    username = payload.get("sub")
    role = payload.get("role")
    if not username or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = get_user_by_username(session, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not active",
        )

    if user.role != role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role mismatch",
        )

    return user


def require_roles(*allowed_roles: str):
    """
    Use as a dependency to gate endpoints by role.

    Example:
        @router.get("/admin-only", dependencies=[Depends(require_roles("admin", "super-admin"))])
    """
    def _checker(user: Member = Depends(get_current_user)) -> Member:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient privileges",
            )
        return user

    return _checker


async def get_current_user_from_token(
    session: Session,
    authorization: str = Depends(auth_header),
) -> Member:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")

    token = _get_token_from_header(authorization)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    try:
        payload = decode_token(token)
        username = payload.get("sub")
        role = payload.get("role")
        if not username or not role:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    user = get_user_by_username(session, username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not active")

    # Optional consistency check: token role matches DB role
    if user.role != role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role mismatch")

    return user


def authorize(role: str) -> Callable:

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(
            *args: Any,
            current_user=Depends(get_current_user_from_token),
            **kwargs: Any,
        ):
            if current_user.role != role:
                raise HTTPException(status_code=403, detail="Not enough permissions")
            kwargs["current_user"] = current_user

            return func(*args, **kwargs)

        return wrapper

    return decorator
