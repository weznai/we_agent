from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy import text as sa_text
from datetime import datetime, timezone
from ..database import Base, _utcnow


def _now():
    return datetime.now(timezone.utc)


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    knowledge_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("knowledge_groups.id"), nullable=True)
    chunk_index = Column(Integer, default=0)
    content = Column(Text, default="")
    embedding = Column(Text, default="")
    chunk_type = Column(String(20), default="text")
    page_idx = Column(Integer, nullable=True)
    content_path = Column(String(500), default="")
    image_path = Column(String(500), default="")
    metadata_json = Column(Text, default="")
    created_at = Column(DateTime, default=_now, server_default=sa_text("CURRENT_TIMESTAMP"))
