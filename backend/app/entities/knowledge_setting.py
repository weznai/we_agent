from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy import text as sa_text
from datetime import datetime, timezone
from ..database import Base, _utcnow


def _now():
    return datetime.now(timezone.utc)


class KnowledgeSetting(Base):
    __tablename__ = "knowledge_settings"
    __table_args__ = (
        UniqueConstraint("user_id", "group_id", name="uq_knowledge_settings_user_group"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    group_id = Column(Integer, ForeignKey("knowledge_groups.id"), nullable=True, index=True)
    embedding_model_id = Column(Integer, nullable=True)
    enable_rerank = Column(Boolean, default=False)
    rerank_model_id = Column(Integer, nullable=True)
    chunk_method = Column(String(50), default="auto")
    chunk_size = Column(Integer, default=500)
    chunk_overlap = Column(Integer, default=50)
    retrieval_method = Column(String(50), default="pure")
    retrieval_top_k = Column(Integer, default=5)
    score_threshold = Column(String(10), default="0.5")
    created_at = Column(DateTime, default=_now, server_default=sa_text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, default=_now, onupdate=_now, server_default=sa_text("CURRENT_TIMESTAMP"))
