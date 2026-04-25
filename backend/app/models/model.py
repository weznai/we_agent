from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy import text as sa_text
from datetime import datetime, timezone
from ..database import Base, _utcnow


def _now():
    return datetime.now(timezone.utc)


class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=True)
    name = Column(String(100), nullable=False)
    display_name = Column(String(100), default="")
    model_type = Column(String(50), default="chat")
    description = Column(Text, default="")
    max_tokens = Column(Integer, default=4096)
    temperature = Column(String(10), default="0.7")
    embedding_dimension = Column(Integer, default=0)
    model_path = Column(String(500), default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_now, server_default=sa_text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, default=_now, onupdate=_now, server_default=sa_text("CURRENT_TIMESTAMP"))
