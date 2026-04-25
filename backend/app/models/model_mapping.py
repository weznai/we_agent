from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy import text as sa_text
from datetime import datetime, timezone
from ..database import Base, _utcnow


def _now():
    return datetime.now(timezone.utc)


class ModelMapping(Base):
    __tablename__ = "model_mappings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    agent_type = Column(String(50), nullable=False)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=_now, server_default=sa_text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, default=_now, onupdate=_now, server_default=sa_text("CURRENT_TIMESTAMP"))
