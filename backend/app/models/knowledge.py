from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy import text as sa_text
from datetime import datetime, timezone
from ..database import Base, _utcnow


def _now():
    return datetime.now(timezone.utc)


class Knowledge(Base):
    __tablename__ = "knowledge_bases"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("knowledge_groups.id"), nullable=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    file_path = Column(String(500), default="")
    file_type = Column(String(20), default="")
    file_size = Column(Integer, default=0)
    content = Column(Text, default="")
    chunk_count = Column(Integer, default=0)
    status = Column(String(20), default="active")
    indexed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_now, server_default=sa_text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, default=_now, onupdate=_now, server_default=sa_text("CURRENT_TIMESTAMP"))
