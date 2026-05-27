import re
from typing import Optional

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, EmailStr, field_validator

from app.schemas import BaseSerializer

USERNAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class LoginBase(BaseSerializer):
    username: str
    password: str


class SignUpBase(BaseSerializer):
    username: str = Field(min_length=4, max_length=30)
    password: str = Field(min_length=8, max_length=30)
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not USERNAME_RE.match(v):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Username must be letters and '_' with optional digits ONLY at the end. "
                       "'_' cannot be first."
            )
        return v


class MemberResponse(BaseModel):
    id: int
    username: str
    role: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"