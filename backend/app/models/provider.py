from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy import text as sa_text
from datetime import datetime, timezone
from ..database import Base, _utcnow


def _now():
    return datetime.now(timezone.utc)


class Provider(Base):
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(100), default="")
    description = Column(Text, default="")
    api_base = Column(String(500), default="")
    api_key = Column(String(500), default="")
    logo = Column(String(255), default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_now, server_default=sa_text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, default=_now, onupdate=_now, server_default=sa_text("CURRENT_TIMESTAMP"))
