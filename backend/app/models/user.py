import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text
from sqlalchemy import text as sa_text
from datetime import datetime, timezone
from ..database import Base, _utcnow


class UserRole(str, enum.Enum):
    SUPER = "super"
    ADMIN = "admin"
    USER = "user"


def _now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    nickname = Column(String(50), default="")
    avatar = Column(String(255), default="")
    role = Column(String(20), default=UserRole.USER.value)
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_now, server_default=sa_text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, default=_now, onupdate=_now, server_default=sa_text("CURRENT_TIMESTAMP"))
