from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy import text as sa_text
from datetime import datetime, timezone
from ..database import Base, _utcnow


def _now():
    return datetime.now(timezone.utc)


class KnowledgeGroup(Base):
    __tablename__ = "knowledge_groups"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    color = Column(String(20), default="#6366f1")
    icon = Column(String(50), default="Folder")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=_now, server_default=sa_text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, default=_now, onupdate=_now, server_default=sa_text("CURRENT_TIMESTAMP"))
