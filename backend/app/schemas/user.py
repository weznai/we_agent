from pydantic import BaseModel, EmailStr, field_serializer
from typing import Optional
from datetime import datetime
from ..entities import UserRole


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    verification_code: Optional[str] = None


class UserLogin(BaseModel):
    login: str
    password: str


class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    email: Optional[EmailStr] = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    nickname: str
    avatar: str
    role: UserRole
    is_active: bool
    email_verified: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @field_serializer('role')
    def serialize_role(self, v):
        return v.value if hasattr(v, 'value') else v


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
